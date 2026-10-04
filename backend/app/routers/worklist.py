from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.clock import facility_today
from app.core.config import settings
from app.core.security import get_current_user
from app.database import get_db
from app.models.models import (
    DischargePlan,
    DischargePlanStatus,
    NudgeLog,
    Patient,
    PostnatalVisit,
    RiskFlag,
    RiskFlagType,
    StaffUser,
    VisitStatus,
)
from app.schemas.schemas import WorklistItem, WorklistOut, WorklistSummary
from app.services.calendar_engine import HIGH_RISK_FLAGS, days_overdue, refresh_facility_statuses

router = APIRouter(prefix=f"{settings.API_V1_STR}/worklist", tags=["worklist"])


def _facility_visits(db: Session, facility_id: int):
    return (
        db.query(PostnatalVisit)
        .join(DischargePlan)
        .join(Patient, DischargePlan.patient_id == Patient.patient_id)
        .filter(Patient.facility_id == facility_id, DischargePlan.status == DischargePlanStatus.ACTIVE.value)
    )


@router.get("", response_model=WorklistOut)
def get_ranked_worklist(
    visit_type: str | None = Query(None, description="Exact visit type, e.g. '24h Checkup'"),
    risk_flag: RiskFlagType | None = Query(None),
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    """FR-008 / FR-009: every due-today or overdue visit at the user's facility,
    most overdue first, optionally filtered by visit type or risk flag."""
    today = facility_today()
    refresh_facility_statuses(db, current_user.facility_id, today)
    base = _facility_visits(db, current_user.facility_id)

    query = base.filter(PostnatalVisit.status.in_([VisitStatus.OVERDUE.value, VisitStatus.DUE_TODAY.value]))
    if visit_type:
        query = query.filter(PostnatalVisit.visit_type == visit_type)
    if risk_flag:
        query = query.filter(DischargePlan.risk_flags.any(RiskFlag.flag_type == risk_flag.value))

    visits = query.options(joinedload(PostnatalVisit.plan).joinedload(DischargePlan.patient)).all()

    last_nudges: dict[int, NudgeLog] = {}
    if visits:
        latest_ids = (
            db.query(func.max(NudgeLog.nudge_id))
            .filter(NudgeLog.visit_id.in_([v.visit_id for v in visits]), NudgeLog.recipient_type == "mother")
            .group_by(NudgeLog.visit_id)
        )
        for nudge in db.query(NudgeLog).filter(NudgeLog.nudge_id.in_(latest_ids)).all():
            last_nudges[nudge.visit_id] = nudge

    items = []
    for visit in visits:
        patient = visit.plan.patient
        last = last_nudges.get(visit.visit_id)
        items.append(
            WorklistItem(
                patient_id=patient.patient_id,
                patient_name=patient.name,
                contact_number=patient.contact_number,
                preferred_language=patient.preferred_language,
                visit_id=visit.visit_id,
                visit_type=visit.visit_type,
                due_date=visit.due_date,
                days_overdue=days_overdue(visit.due_date, today),
                status=visit.status,
                risk_flags=sorted({rf.flag_type for rf in visit.plan.risk_flags}),
                last_reminder_at=last.sent_at if last else None,
                last_reminder_status=last.status if last else None,
            )
        )
    items.sort(key=lambda i: (-i.days_overdue, i.due_date, i.patient_name))

    # Summary counts ignore the filters so the header numbers stay stable.
    open_visits = base.filter(PostnatalVisit.status.in_([VisitStatus.OVERDUE.value, VisitStatus.DUE_TODAY.value])).all()
    summary = WorklistSummary(
        overdue=sum(1 for v in open_visits if v.status == VisitStatus.OVERDUE.value),
        due_today=sum(1 for v in open_visits if v.status == VisitStatus.DUE_TODAY.value),
        high_risk=len(
            {v.plan.patient_id for v in open_visits if {rf.flag_type for rf in v.plan.risk_flags} & HIGH_RISK_FLAGS}
        ),
        upcoming_7_days=base.filter(
            PostnatalVisit.status == VisitStatus.UPCOMING.value,
            PostnatalVisit.due_date <= today + timedelta(days=7),
        ).count(),
    )
    return WorklistOut(as_of=today, summary=summary, items=items)
