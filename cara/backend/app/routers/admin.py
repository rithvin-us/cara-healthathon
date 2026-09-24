from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models.models import StaffUser, Facility, AuditLog
from app.schemas.schemas import StaffUserCreate, StaffUserOut
from app.core.security import get_current_user, require_role, get_password_hash
from app.core.config import settings
from app.services.calendar_engine import CalendarEngine
from app.services.nudge_engine import NudgeEngine
from app.services.digest_service import DigestService

router = APIRouter(prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])

@router.get("/staff", response_model=List[StaffUserOut])
def get_facility_staff(
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role(["Admin"]))
):
    """
    FR-022: List staff accounts for facility.
    """
    staff = db.query(StaffUser).filter(StaffUser.facility_id == current_user.facility_id).all()
    return staff

@router.post("/staff", response_model=StaffUserOut, status_code=status.HTTP_201_CREATED)
def create_staff_account(
    staff_in: StaffUserCreate,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role(["Admin"]))
):
    """
    FR-022: Facility Admin creates staff account with role assignment (Doctor / Coordinator / Admin).
    """
    existing = db.query(StaffUser).filter(StaffUser.email == staff_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Staff account with this email already exists")

    user = StaffUser(
        facility_id=current_user.facility_id,
        name=staff_in.name,
        role=staff_in.role,
        email=staff_in.email,
        password_hash=get_password_hash(staff_in.password),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit = AuditLog(
        actor_id=current_user.user_id,
        action="CREATE_STAFF_USER",
        entity="StaffUser",
        entity_id=user.user_id,
        details=f"Created staff account {user.email} with role {user.role}"
    )
    db.add(audit)
    db.commit()

    return user

@router.patch("/staff/{user_id}/toggle-active", response_model=StaffUserOut)
def toggle_staff_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role(["Admin"]))
):
    """
    FR-022: Deactivate or activate staff account.
    """
    user = db.query(StaffUser).filter(
        StaffUser.user_id == user_id,
        StaffUser.facility_id == current_user.facility_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Staff user not found")

    user.is_active = not user.is_active
    db.commit()

    audit = AuditLog(
        actor_id=current_user.user_id,
        action="TOGGLE_STAFF_ACTIVE",
        entity="StaffUser",
        entity_id=user.user_id,
        details=f"Toggled active state to {user.is_active} for staff user {user.email}"
    )
    db.add(audit)
    db.commit()

    return user

@router.get("/digest")
def get_weekly_digest(
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user)
):
    """
    FR-012: Generate Weekly Plain-Language Digest for facility coordinator.
    """
    return DigestService.generate_weekly_digest(db, current_user.facility_id)

@router.post("/scheduler/run")
def trigger_daily_scheduler(
    simulate_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role(["Admin", "Doctor", "Coordinator"]))
):
    """
    Triggers daily status computation job (FR-005) and batch nudge sending (FR-011).
    Allows simulate_date for testing future visit transitions!
    """
    target_date = simulate_date or date.today()
    updated_visits = CalendarEngine.recompute_all_visit_statuses(db, target_date)
    sent_nudges = NudgeEngine.trigger_batch_nudges(db)

    return {
        "status": "completed",
        "simulated_date": target_date,
        "visits_status_updated": updated_visits,
        "batch_nudges_sent": sent_nudges
    }
