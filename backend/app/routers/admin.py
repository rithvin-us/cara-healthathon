from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.clock import facility_today
from app.core.config import settings
from app.core.security import get_current_user, get_password_hash, require_role
from app.database import get_db
from app.models.models import StaffRole, StaffUser
from app.schemas.schemas import DigestOut, SchedulerRunOut, StaffUserCreate, StaffUserOut
from app.services import audit, calendar_engine
from app.services.digest_service import DigestService
from app.services.nudge_engine import NudgeEngine

router = APIRouter(prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])

ADMIN_ONLY = require_role([StaffRole.ADMIN])


@router.get("/staff", response_model=list[StaffUserOut])
def get_facility_staff(db: Session = Depends(get_db), current_user: StaffUser = Depends(ADMIN_ONLY)):
    """FR-022: staff accounts at the admin's facility."""
    return (
        db.query(StaffUser).filter(StaffUser.facility_id == current_user.facility_id).order_by(StaffUser.user_id).all()
    )


@router.post("/staff", response_model=StaffUserOut, status_code=status.HTTP_201_CREATED)
def create_staff_account(
    staff_in: StaffUserCreate,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(ADMIN_ONLY),
):
    """FR-022: create a Doctor, Coordinator or Admin account at this facility."""
    email = staff_in.email.lower()
    if db.query(StaffUser).filter(StaffUser.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    user = StaffUser(
        facility_id=current_user.facility_id,
        name=staff_in.name,
        role=staff_in.role.value,
        email=email,
        password_hash=get_password_hash(staff_in.password),
        is_active=True,
    )
    db.add(user)
    db.flush()
    audit.record(
        db,
        actor=current_user,
        action="CREATE_STAFF_USER",
        entity="StaffUser",
        entity_id=user.user_id,
        details=f"Created {user.role} account {user.email}",
    )
    db.commit()
    db.refresh(user)
    return user


@router.patch("/staff/{user_id}/toggle-active", response_model=StaffUserOut)
def toggle_staff_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(ADMIN_ONLY),
):
    """FR-022: turn a staff account off or back on."""
    user = (
        db.query(StaffUser)
        .filter(StaffUser.user_id == user_id, StaffUser.facility_id == current_user.facility_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Staff account not found")
    if user.user_id == current_user.user_id:
        raise HTTPException(status_code=409, detail="You can't turn off your own account.")

    user.is_active = not user.is_active
    audit.record(
        db,
        actor=current_user,
        action="TOGGLE_STAFF_ACTIVE",
        entity="StaffUser",
        entity_id=user.user_id,
        details=f"Access {'turned on' if user.is_active else 'turned off'} for {user.email}",
    )
    db.commit()
    db.refresh(user)
    return user


@router.get("/digest", response_model=DigestOut)
def get_weekly_digest(db: Session = Depends(get_db), current_user: StaffUser = Depends(get_current_user)):
    """FR-012: plain-language weekly digest for the facility."""
    return DigestService.generate_weekly_digest(db, current_user.facility_id)


def run_daily_job(db: Session, run_date: date, facility_id: int | None, actor: StaffUser | None) -> SchedulerRunOut:
    updated = calendar_engine.recompute_all_visit_statuses(db, run_date, facility_id=facility_id)
    if updated:
        audit.record(
            db,
            actor=actor,
            facility_id=facility_id,
            action="RECOMPUTE_VISIT_STATUSES",
            entity="PostnatalVisit",
            details=f"{updated} visit statuses updated for {run_date.isoformat()}",
        )
    sent = NudgeEngine.trigger_batch_nudges(db, facility_id=facility_id)
    db.commit()
    return SchedulerRunOut(status="completed", run_date=run_date, visits_status_updated=updated, batch_nudges_sent=sent)


@router.post("/scheduler/run", response_model=SchedulerRunOut)
def trigger_daily_scheduler(
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role([StaffRole.ADMIN, StaffRole.DOCTOR, StaffRole.COORDINATOR])),
):
    """Runs the daily job for this facility now: refresh visit statuses (FR-005),
    then send due-today / newly-overdue reminders (FR-011). Safe to re-run: a
    visit never gets the same scheduled reminder twice."""
    return run_daily_job(db, facility_today(), current_user.facility_id, current_user)


@router.post("/demo/reset", status_code=status.HTTP_200_OK)
def reset_demo_data(_: StaffUser = Depends(ADMIN_ONLY)):
    """Demo mode only: wipe the database and reload the synthetic patients, so a
    walkthrough can be recorded again from a known starting point."""
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=404, detail="Not found")
    from app.seed import reset_and_seed

    summary = reset_and_seed()
    return {"status": "reset", **summary}
