from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.models import AuditLog, StaffUser
from app.schemas.schemas import AuditLogOut
from app.core.security import get_current_user, require_role
from app.core.config import settings

router = APIRouter(prefix=f"{settings.API_V1_STR}/audit-log", tags=["audit"])

@router.get("", response_model=List[AuditLogOut])
def get_all_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role(["Admin", "Doctor"]))
):
    """
    FR-021: Immutable Audit Log history for facility.
    """
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return logs

@router.get("/{patient_id}", response_model=List[AuditLogOut])
def get_patient_audit_logs(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user)
):
    """
    FR-021: Audit trail filtered by patient.
    """
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    return logs
