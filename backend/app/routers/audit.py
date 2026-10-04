from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.access import get_patient_or_404
from app.core.config import settings
from app.core.security import get_current_user, require_role
from app.database import get_db
from app.models.models import AuditLog, StaffRole, StaffUser
from app.schemas.schemas import AuditLogOut

router = APIRouter(prefix=f"{settings.API_V1_STR}/audit-log", tags=["audit"])


def _with_actor_names(db: Session, logs: list[AuditLog]) -> list[AuditLogOut]:
    actor_ids = {log.actor_id for log in logs if log.actor_id}
    names = (
        {u.user_id: u.name for u in db.query(StaffUser).filter(StaffUser.user_id.in_(actor_ids)).all()}
        if actor_ids
        else {}
    )
    out = []
    for log in logs:
        item = AuditLogOut.model_validate(log)
        item.actor_name = "System" if not log.actor_id else names.get(log.actor_id, f"User #{log.actor_id}")
        out.append(item)
    return out


@router.get("", response_model=list[AuditLogOut])
def get_facility_audit_log(
    limit: int = Query(100, ge=1, le=500),
    action: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role([StaffRole.ADMIN, StaffRole.DOCTOR])),
):
    """FR-021: the facility's append-only audit trail, newest first."""
    query = db.query(AuditLog).filter(AuditLog.facility_id == current_user.facility_id)
    if action:
        query = query.filter(AuditLog.action == action)
    logs = query.order_by(AuditLog.timestamp.desc(), AuditLog.audit_id.desc()).limit(limit).all()
    return _with_actor_names(db, logs)


@router.get("/patients/{patient_id}", response_model=list[AuditLogOut])
def get_patient_audit_log(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    """FR-021: every change made to one mother's plan, visits and consent."""
    patient = get_patient_or_404(db, patient_id, current_user)
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.patient_id == patient.patient_id, AuditLog.facility_id == current_user.facility_id)
        .order_by(AuditLog.timestamp.desc(), AuditLog.audit_id.desc())
        .all()
    )
    return _with_actor_names(db, logs)
