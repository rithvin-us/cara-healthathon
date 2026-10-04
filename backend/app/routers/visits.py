from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.access import get_visit_or_404
from app.core.clock import facility_today
from app.core.config import settings
from app.core.security import require_role
from app.database import get_db
from app.models.models import (
    CLOSED_VISIT_STATUSES,
    DischargePlanStatus,
    PostnatalVisit,
    StaffRole,
    StaffUser,
    VisitStatus,
)
from app.schemas.schemas import (
    MessagePreviewOut,
    NudgeLogOut,
    VisitActionOut,
    VisitCompleteRequest,
    VisitMissedRequest,
    VisitRescheduleRequest,
)
from app.services import audit, calendar_engine
from app.services.content_filter import ContentFilter
from app.services.message_templates import describe_visit, format_date
from app.services.nudge_engine import NudgeEngine

router = APIRouter(prefix=f"{settings.API_V1_STR}/visits", tags=["visits"])

CARE_TEAM = require_role([StaffRole.COORDINATOR, StaffRole.DOCTOR, StaffRole.ADMIN])

_MISSED_REASON_TEXT = {
    "unreachable": "couldn't be reached",
    "declined": "declined the visit",
    "moved": "moved away",
}


def _ensure_open(visit: PostnatalVisit) -> None:
    if visit.status in CLOSED_VISIT_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This visit is already marked {visit.status}.",
        )
    if visit.plan.status != DischargePlanStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Her discharge plan is closed.")


def _action_out(visit: PostnatalVisit, audit_id: int) -> VisitActionOut:
    return VisitActionOut(
        visit_id=visit.visit_id,
        status=visit.status,
        due_date=visit.due_date,
        completed_date=visit.completed_date,
        audit_id=audit_id,
    )


@router.post("/{visit_id}/complete", response_model=VisitActionOut)
def mark_visit_complete(
    visit_id: int,
    req: VisitCompleteRequest,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(CARE_TEAM),
):
    """FR-006: record a completed visit. The note is logistics only and is
    rejected if it contains clinical terms (AI-006)."""
    visit = get_visit_or_404(db, visit_id, current_user)
    _ensure_open(visit)

    patient = visit.plan.patient
    if req.completed_date > facility_today():
        raise HTTPException(status_code=422, detail="The visit date can't be in the future.")
    if req.completed_date < patient.delivery_date:
        raise HTTPException(status_code=422, detail="The visit date can't be before the delivery date.")
    if req.note:
        is_valid, reason = ContentFilter.inspect_text(req.note)
        if not is_valid:
            raise HTTPException(
                status_code=422,
                detail=f"Note rejected: write logistics only (where and how she was seen). {reason}",
            )

    visit.status = VisitStatus.COMPLETED.value
    visit.completed_date = req.completed_date
    visit.note = req.note or None
    entry = audit.record(
        db,
        actor=current_user,
        action="MARK_VISIT_COMPLETE",
        entity="PostnatalVisit",
        entity_id=visit.visit_id,
        patient_id=patient.patient_id,
        details=f"{describe_visit(visit.visit_type)} marked done on {format_date(req.completed_date, 'English')}",
    )
    db.commit()
    return _action_out(visit, entry.audit_id)


@router.post("/{visit_id}/missed", response_model=VisitActionOut)
def mark_visit_missed(
    visit_id: int,
    req: VisitMissedRequest,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(CARE_TEAM),
):
    """FR-007: record that a visit couldn't happen, with an operational reason."""
    visit = get_visit_or_404(db, visit_id, current_user)
    _ensure_open(visit)

    visit.status = VisitStatus.MISSED.value
    visit.note = f"Missed: {_MISSED_REASON_TEXT[req.reason.value]}"
    entry = audit.record(
        db,
        actor=current_user,
        action="MARK_VISIT_MISSED",
        entity="PostnatalVisit",
        entity_id=visit.visit_id,
        patient_id=visit.plan.patient_id,
        details=f"{describe_visit(visit.visit_type)} marked missed: she {_MISSED_REASON_TEXT[req.reason.value]}",
    )
    db.commit()
    return _action_out(visit, entry.audit_id)


@router.patch("/{visit_id}/reschedule", response_model=VisitActionOut)
def reschedule_visit(
    visit_id: int,
    req: VisitRescheduleRequest,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role([StaffRole.DOCTOR, StaffRole.COORDINATOR])),
):
    """FR-003: move a visit to a new date (e.g. the mother was readmitted)."""
    visit = get_visit_or_404(db, visit_id, current_user)
    _ensure_open(visit)

    patient = visit.plan.patient
    if req.due_date < patient.delivery_date:
        raise HTTPException(status_code=422, detail="The new date can't be before the delivery date.")
    if any(v.due_date == req.due_date and v.visit_id != visit.visit_id for v in visit.plan.visits):
        raise HTTPException(status_code=409, detail="She already has a visit on that date.")

    old_date = visit.due_date
    visit.due_date = req.due_date
    visit.status = calendar_engine.status_for(req.due_date, facility_today())
    entry = audit.record(
        db,
        actor=current_user,
        action="RESCHEDULE_VISIT",
        entity="PostnatalVisit",
        entity_id=visit.visit_id,
        patient_id=patient.patient_id,
        details=(
            f"{describe_visit(visit.visit_type)} moved from {format_date(old_date, 'English')} "
            f"to {format_date(req.due_date, 'English')}"
        ),
    )
    db.commit()
    return _action_out(visit, entry.audit_id)


@router.get("/{visit_id}/message-preview", response_model=MessagePreviewOut)
def preview_message(
    visit_id: int,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(CARE_TEAM),
):
    """The exact WhatsApp text the mother would receive for this visit right now."""
    visit = get_visit_or_404(db, visit_id, current_user)
    patient = visit.plan.patient
    return MessagePreviewOut(
        visit_id=visit.visit_id,
        recipient_name=patient.name,
        recipient_contact=patient.contact_number,
        language=patient.preferred_language,
        channel="whatsapp",
        message_text=NudgeEngine.compose_mother_message(visit, patient),
        provider="twilio" if settings.twilio_enabled else "simulated",
    )


@router.post("/{visit_id}/nudge", response_model=list[NudgeLogOut])
def manual_retrigger_nudge(
    visit_id: int,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(CARE_TEAM),
):
    """FR-014: coordinator re-sends a reminder for one visit."""
    visit = get_visit_or_404(db, visit_id, current_user)
    _ensure_open(visit)
    nudges = NudgeEngine.trigger_nudge_for_visit(db, visit, trigger="manual", actor=current_user)
    db.commit()
    return [NudgeLogOut.model_validate(n) for n in nudges]
