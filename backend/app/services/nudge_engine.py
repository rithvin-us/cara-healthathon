"""Nudge & communication engine (FR-011, FR-013, FR-014, FR-017).

Sends WhatsApp reminders with SMS fallback. With NUDGE_PROVIDER=simulated (the
default) messages are composed, filtered and logged exactly as in production
but not handed to Twilio, so demos never message a real phone.
"""

import logging
import uuid
from dataclasses import dataclass

import requests
from sqlalchemy.orm import Session

from app.core.clock import facility_today
from app.core.config import settings
from app.models.models import (
    ConsentRecord,
    DischargePlan,
    DischargePlanStatus,
    FamilyMember,
    NudgeLog,
    Patient,
    PostnatalVisit,
    VisitStatus,
)
from app.services import audit, message_templates
from app.services.content_filter import ContentFilter

logger = logging.getLogger("cara.nudges")

TWILIO_API = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
_TRIGGER_TEXT = {"due_today": "Due-day", "overdue": "Late", "manual": "Manual"}


@dataclass
class SendResult:
    ok: bool
    channel: str
    status: str
    provider_message_id: str | None = None
    error: str | None = None


class NudgeEngine:
    # --- consent ---------------------------------------------------------
    @staticmethod
    def is_family_consent_active(db: Session, family_id: int) -> bool:
        """Consent is a hard gate: no family nudge without a latest ConsentRecord of True."""
        latest = (
            db.query(ConsentRecord)
            .filter(ConsentRecord.family_id == family_id)
            .order_by(ConsentRecord.consent_id.desc())
            .first()
        )
        return latest is not None and latest.consent_given is True

    # --- composing -------------------------------------------------------
    @staticmethod
    def compose_mother_message(visit: PostnatalVisit, patient: Patient, today=None) -> str:
        today = today or facility_today()
        facility_name = patient.facility.name if patient.facility else "the hospital"
        kind = "mother_overdue" if visit.due_date < today else "mother_due"
        text = message_templates.render(
            kind,
            patient.preferred_language,
            name=patient.name,
            facility=facility_name,
            visit_type=visit.visit_type,
            due_date=visit.due_date,
        )
        final, _ = ContentFilter.filter_and_fallback_nudge(
            text,
            mother_name=patient.name,
            visit_type=message_templates.visit_label(visit.visit_type, "English"),
            due_date=message_templates.format_date(visit.due_date, "English"),
            facility_name=facility_name,
        )
        return final

    @staticmethod
    def compose_family_message(visit: PostnatalVisit, patient: Patient, member: FamilyMember, today=None) -> str:
        today = today or facility_today()
        facility_name = patient.facility.name if patient.facility else "the hospital"
        text = message_templates.render(
            "family_overdue" if visit.due_date < today else "family",
            member.preferred_language,
            name=member.name,
            facility=facility_name,
            visit_type=visit.visit_type,
            due_date=visit.due_date,
            mother=patient.name,
        )
        final, _ = ContentFilter.filter_and_fallback_nudge(
            text,
            mother_name=patient.name,
            visit_type=message_templates.visit_label(visit.visit_type, "English"),
            due_date=message_templates.format_date(visit.due_date, "English"),
            facility_name=facility_name,
        )
        return final

    # --- sending ---------------------------------------------------------
    @staticmethod
    def _valid_contact(contact: str) -> bool:
        digits = "".join(ch for ch in contact or "" if ch.isdigit())
        return (contact or "").startswith("+") and 10 <= len(digits) <= 15

    @staticmethod
    def _twilio_send(to: str, body: str, channel: str) -> SendResult:
        sender = settings.TWILIO_WHATSAPP_NUMBER if channel == "whatsapp" else settings.TWILIO_SMS_NUMBER
        if not sender:
            return SendResult(False, channel, "failed", error=f"No Twilio {channel} sender configured")
        data = {
            "From": sender,
            "To": f"whatsapp:{to}" if channel == "whatsapp" else to,
            "Body": body,
        }
        if settings.TWILIO_STATUS_CALLBACK_URL:
            data["StatusCallback"] = settings.TWILIO_STATUS_CALLBACK_URL
        try:
            resp = requests.post(
                TWILIO_API.format(sid=settings.TWILIO_ACCOUNT_SID),
                data=data,
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                timeout=10,
            )
        except requests.RequestException as exc:
            logger.warning("Twilio %s send failed: %s", channel, exc)
            return SendResult(False, channel, "failed", error=str(exc))
        if resp.status_code >= 400:
            logger.warning("Twilio %s send rejected (%s): %s", channel, resp.status_code, resp.text[:300])
            return SendResult(False, channel, "failed", error=f"Twilio HTTP {resp.status_code}")
        payload = resp.json()
        return SendResult(True, channel, payload.get("status", "queued"), provider_message_id=payload.get("sid"))

    @staticmethod
    def send_message(contact: str, body: str) -> SendResult:
        """WhatsApp first, SMS on failure (FR-011 alternative flow)."""
        if not NudgeEngine._valid_contact(contact):
            return SendResult(False, "whatsapp", "failed", error="invalid_contact_number")

        if not settings.twilio_enabled:
            return SendResult(True, "whatsapp", "delivered", provider_message_id=f"SIM{uuid.uuid4().hex[:30]}")

        result = NudgeEngine._twilio_send(contact, body, "whatsapp")
        if not result.ok:
            sms = NudgeEngine._twilio_send(contact, body, "sms")
            if sms.ok:
                return sms
        return result

    # --- orchestration ---------------------------------------------------
    @staticmethod
    def trigger_nudge_for_visit(db: Session, visit: PostnatalVisit, trigger: str, actor=None) -> list[NudgeLog]:
        """Sends to the mother and every consented family member. `trigger` is
        'due_today', 'overdue' (scheduled job) or 'manual' (FR-014)."""
        patient = visit.plan.patient
        created: list[NudgeLog] = []

        recipients = [("mother", patient.contact_number, NudgeEngine.compose_mother_message(visit, patient))]
        for member in patient.family_members:
            if NudgeEngine.is_family_consent_active(db, member.family_id):
                recipients.append(
                    ("family", member.contact_number, NudgeEngine.compose_family_message(visit, patient, member))
                )

        for recipient_type, contact, text in recipients:
            result = NudgeEngine.send_message(contact, text)
            log = NudgeLog(
                visit_id=visit.visit_id,
                channel=result.channel,
                recipient_type=recipient_type,
                recipient_contact=contact,
                status=result.status if result.ok else "failed",
                message_text=text,
                provider_message_id=result.provider_message_id,
                trigger=trigger,
            )
            db.add(log)
            created.append(log)

        db.flush()
        delivered = sum(1 for n in created if n.status != "failed")
        audit.record(
            db,
            action="TRIGGER_NUDGE",
            entity="PostnatalVisit",
            entity_id=visit.visit_id,
            details=(
                f"{_TRIGGER_TEXT.get(trigger, trigger)} reminder for {message_templates.describe_visit(visit.visit_type)}: "
                f"{delivered} of {len(created)} messages sent"
            ),
            actor=actor,
            facility_id=patient.facility_id,
            patient_id=patient.patient_id,
        )
        return created

    @staticmethod
    def trigger_batch_nudges(db: Session, facility_id: int | None = None) -> int:
        """Scheduled run: one reminder when a visit becomes due today and one when it
        first turns overdue. Re-running the job the same day sends nothing new."""
        query = (
            db.query(PostnatalVisit)
            .join(DischargePlan)
            .join(Patient, DischargePlan.patient_id == Patient.patient_id)
            .filter(
                DischargePlan.status == DischargePlanStatus.ACTIVE.value,
                PostnatalVisit.status.in_([VisitStatus.DUE_TODAY.value, VisitStatus.OVERDUE.value]),
            )
        )
        if facility_id is not None:
            query = query.filter(Patient.facility_id == facility_id)

        total = 0
        for visit in query.all():
            already_sent = (
                db.query(NudgeLog.nudge_id)
                .filter(NudgeLog.visit_id == visit.visit_id, NudgeLog.trigger == visit.status)
                .first()
            )
            if already_sent:
                continue
            total += len(NudgeEngine.trigger_nudge_for_visit(db, visit, trigger=visit.status))
        return total
