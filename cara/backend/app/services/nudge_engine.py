from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.models import PostnatalVisit, Patient, FamilyMember, ConsentRecord, NudgeLog, AuditLog, VisitStatus, Facility
from app.services.content_filter import ContentFilter
import requests

class NudgeEngine:
    @staticmethod
    def is_family_consent_active(db: Session, family_id: int) -> bool:
        """
        Consent is a hard gate: API rejects any nudge-send attempt to a FamilyMember
        without an active ConsentRecord where consent_given is True.
        """
        latest_consent = db.query(ConsentRecord).filter(
            ConsentRecord.family_id == family_id
        ).order_by(ConsentRecord.timestamp.desc()).first()

        return latest_consent is not None and latest_consent.consent_given is True

    @staticmethod
    def send_twilio_message(contact: str, message: str, channel: str = "whatsapp") -> Tuple[bool, str]:
        """
        Mock/Actual Twilio sending logic. Returns (success, status_or_sid)
        """
        # Simulated send response (in production environment, uses Twilio REST client)
        if not contact or len(contact) < 5:
            return False, "invalid_contact_number"
        return True, "delivered"

    @staticmethod
    def trigger_nudge_for_visit(db: Session, visit_id: int, manual_trigger: bool = False) -> List[NudgeLog]:
        """
        Triggers nudges for a visit to mother and any consented family members.
        Returns list of created NudgeLog records.
        """
        visit = db.query(PostnatalVisit).filter(PostnatalVisit.visit_id == visit_id).first()
        if not visit:
            return []

        patient = visit.plan.patient
        facility = patient.facility
        facility_name = facility.name if facility else "Cara Health Clinic"

        # Check visit status eligibility unless manual trigger
        if not manual_trigger and visit.status not in [VisitStatus.DUE_TODAY.value, VisitStatus.OVERDUE.value]:
            return []

        nudges_created = []

        # 1. Mother Nudge
        mother_raw_text = f"Hello {patient.name}, your {visit.visit_type} is scheduled for {visit.due_date.strftime('%b %d, %Y')} at {facility_name}. Please contact us if you need assistance."
        final_mother_text, is_fallback = ContentFilter.filter_and_fallback_nudge(
            generated_text=mother_raw_text,
            mother_name=patient.name,
            visit_type=visit.visit_type,
            due_date=visit.due_date.strftime("%b %d, %Y"),
            facility_name=facility_name
        )

        success, status_str = NudgeEngine.send_twilio_message(patient.contact_number, final_mother_text, channel="whatsapp")
        if not success:
            # Fallback to SMS
            success, status_str = NudgeEngine.send_twilio_message(patient.contact_number, final_mother_text, channel="sms")
            channel_used = "sms"
        else:
            channel_used = "whatsapp"

        mother_nudge = NudgeLog(
            visit_id=visit.visit_id,
            channel=channel_used,
            recipient_type="mother",
            recipient_contact=patient.contact_number,
            sent_at=datetime.utcnow(),
            status=status_str if success else "failed",
            message_text=final_mother_text
        )
        db.add(mother_nudge)
        nudges_created.append(mother_nudge)

        # 2. Family Member Nudges (strictly gated by consent)
        family_members = db.query(FamilyMember).filter(FamilyMember.patient_id == patient.patient_id).all()
        for fm in family_members:
            if NudgeEngine.is_family_consent_active(db, fm.family_id):
                family_raw_text = f"Hello {fm.name}, reminder: {patient.name}'s {visit.visit_type} is scheduled for {visit.due_date.strftime('%b %d, %Y')} at {facility_name}."
                final_fm_text, _ = ContentFilter.filter_and_fallback_nudge(
                    generated_text=family_raw_text,
                    mother_name=patient.name,
                    visit_type=visit.visit_type,
                    due_date=visit.due_date.strftime("%b %d, %Y"),
                    facility_name=facility_name
                )
                fm_success, fm_status = NudgeEngine.send_twilio_message(fm.contact_number, final_fm_text, channel="whatsapp")
                if not fm_success:
                    fm_success, fm_status = NudgeEngine.send_twilio_message(fm.contact_number, final_fm_text, channel="sms")
                    fm_channel = "sms"
                else:
                    fm_channel = "whatsapp"

                fm_nudge = NudgeLog(
                    visit_id=visit.visit_id,
                    channel=fm_channel,
                    recipient_type="family",
                    recipient_contact=fm.contact_number,
                    sent_at=datetime.utcnow(),
                    status=fm_status if fm_success else "failed",
                    message_text=final_fm_text
                )
                db.add(fm_nudge)
                nudges_created.append(fm_nudge)

        db.commit()

        # Audit log entry
        audit = AuditLog(
            actor_id=0,
            action="TRIGGER_NUDGE",
            entity="PostnatalVisit",
            entity_id=visit.visit_id,
            details=f"Triggered {len(nudges_created)} nudges for visit #{visit.visit_id}"
        )
        db.add(audit)
        db.commit()

        return nudges_created

    @staticmethod
    def trigger_batch_nudges(db: Session) -> int:
        """
        Runs batch nudge job for all due_today and overdue visits.
        """
        due_or_overdue_visits = db.query(PostnatalVisit).filter(
            PostnatalVisit.status.in_([VisitStatus.DUE_TODAY.value, VisitStatus.OVERDUE.value])
        ).all()

        total_sent = 0
        for visit in due_or_overdue_visits:
            nudges = NudgeEngine.trigger_nudge_for_visit(db, visit.visit_id)
            total_sent += len(nudges)
        return total_sent
