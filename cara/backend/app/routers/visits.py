from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.database import get_db
from app.models.models import PostnatalVisit, VisitStatus, AuditLog, StaffUser, NudgeLog
from app.schemas.schemas import VisitCompleteRequest, VisitMissedRequest, PostnatalVisitOut, NudgeLogOut
from app.core.security import get_current_user, require_role
from app.core.config import settings
from app.services.content_filter import ContentFilter
from app.services.nudge_engine import NudgeEngine

router = APIRouter(prefix=f"{settings.API_V1_STR}/visits", tags=["visits"])

@router.post("/{visit_id}/complete")
def mark_visit_complete(
    visit_id: int,
    req: VisitCompleteRequest,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role(["Coordinator", "Doctor", "Admin"]))
):
    """
    FR-006: Coordinator marks a visit as completed after contact with patient.
    Note field is explicitly rules-filtered to reject clinical terminology.
    """
    visit = db.query(PostnatalVisit).filter(PostnatalVisit.visit_id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    # Content filter on non-clinical note (FR-006 / AI-006)
    note_to_save = req.note
    if req.note and req.note.strip():
        is_valid, reason = ContentFilter.inspect_text(req.note)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Note rejected: Non-clinical notes only. {reason}"
            )

    visit.status = VisitStatus.COMPLETED.value
    visit.completed_date = req.completed_date
    visit.note = note_to_save
    db.commit()

    # Immutable Audit Log (FR-021)
    audit = AuditLog(
        actor_id=current_user.user_id,
        action="MARK_VISIT_COMPLETE",
        entity="PostnatalVisit",
        entity_id=visit.visit_id,
        details=f"Visit #{visit.visit_id} ({visit.visit_type}) marked completed on {req.completed_date.isoformat()}"
    )
    db.add(audit)
    db.commit()

    return {
        "visit_id": visit.visit_id,
        "status": visit.status,
        "completed_date": visit.completed_date,
        "audit_id": audit.audit_id
    }


@router.post("/{visit_id}/missed")
def mark_visit_missed(
    visit_id: int,
    req: VisitMissedRequest,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role(["Coordinator", "Doctor", "Admin"]))
):
    """
    FR-007: Coordinator logs that a visit could not be completed (unreachable/declined/moved).
    """
    visit = db.query(PostnatalVisit).filter(PostnatalVisit.visit_id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    visit.status = VisitStatus.MISSED.value
    visit.note = f"Missed reason: {req.reason}"
    db.commit()

    audit = AuditLog(
        actor_id=current_user.user_id,
        action="MARK_VISIT_MISSED",
        entity="PostnatalVisit",
        entity_id=visit.visit_id,
        details=f"Visit #{visit.visit_id} marked missed: {req.reason}"
    )
    db.add(audit)
    db.commit()

    return {"visit_id": visit.visit_id, "status": visit.status, "audit_id": audit.audit_id}


@router.post("/{visit_id}/nudge", response_model=List[NudgeLogOut])
def manual_retrigger_nudge(
    visit_id: int,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role(["Coordinator", "Doctor", "Admin"]))
):
    """
    FR-014: Coordinator manually re-triggers a nudge for a specific patient/visit.
    """
    nudges = NudgeEngine.trigger_nudge_for_visit(db, visit_id, manual_trigger=True)
    return nudges
