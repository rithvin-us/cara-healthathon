"""Postnatal calendar engine (FR-001, FR-002, FR-005).

The schedule rules live here and nowhere else: the discharge form's preview,
plan creation and risk-flag overrides all call `build_schedule`, so what a
doctor sees on screen is exactly what gets saved.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.clock import facility_today
from app.models.models import (
    OPEN_VISIT_STATUSES,
    DischargePlan,
    DischargePlanStatus,
    Patient,
    PostnatalVisit,
    RiskFlagType,
    VisitStatus,
)
from app.services import audit

# WHO postnatal contacts: 24h, 48-72h, 7-14 days, 6 weeks.
DEFAULT_SCHEDULE = (
    ("24h Checkup", 1),
    ("48-72h Checkup", 3),
    ("7-14d Checkup", 10),
    ("6wk Checkup", 42),
)

# FOGSI-guided extra contacts by risk tier. When several flags apply, the most
# frequent cadence wins; tiers are never averaged (FR-002 exception flow).
HIGH_RISK_FLAGS = {RiskFlagType.HYPERTENSION.value, RiskFlagType.HEMORRHAGE_HISTORY.value}
MODERATE_RISK_FLAGS = {RiskFlagType.ANEMIA.value, RiskFlagType.C_SECTION.value}

RISK_SCHEDULES = {
    "high": (
        ("Weekly Risk Checkup (Week 1)", 7),
        ("Weekly Risk Checkup (Week 2)", 14),
        ("Weekly Risk Checkup (Week 3)", 21),
        ("Weekly Risk Checkup (Week 4)", 28),
    ),
    "moderate": (
        ("Post-op/Anemia Checkup (Week 2)", 14),
        ("Post-op/Anemia Checkup (Week 4)", 28),
    ),
    "specialist": (("Specialist Follow-Up", 14),),
    "standard": (),
}


@dataclass(frozen=True)
class PlannedVisit:
    visit_type: str
    due_date: date
    is_risk_visit: bool


def _flag_values(risk_flags: Iterable) -> set[str]:
    return {getattr(f, "value", f) for f in risk_flags or []}


def risk_tier(risk_flags: Iterable) -> str:
    flags = _flag_values(risk_flags)
    if flags & HIGH_RISK_FLAGS:
        return "high"
    if flags & MODERATE_RISK_FLAGS:
        return "moderate"
    if flags:
        return "specialist"
    return "standard"


def build_schedule(delivery_date: date, risk_flags: Iterable) -> list[PlannedVisit]:
    planned: dict[date, PlannedVisit] = {}
    for visit_type, offset in RISK_SCHEDULES[risk_tier(risk_flags)]:
        due = delivery_date + timedelta(days=offset)
        planned[due] = PlannedVisit(visit_type, due, True)
    for visit_type, offset in DEFAULT_SCHEDULE:
        due = delivery_date + timedelta(days=offset)
        planned.setdefault(due, PlannedVisit(visit_type, due, False))
    return sorted(planned.values(), key=lambda v: v.due_date)


def status_for(due_date: date, today: date) -> str:
    if due_date < today:
        return VisitStatus.OVERDUE.value
    if due_date == today:
        return VisitStatus.DUE_TODAY.value
    return VisitStatus.UPCOMING.value


def create_plan_visits(
    db: Session, plan: DischargePlan, delivery_date: date, risk_flags: Iterable, today: date | None = None
) -> list[PostnatalVisit]:
    """Adds every scheduled visit the plan doesn't already have. Never deletes
    or moves an existing visit, so completed visits and reminder history stay intact."""
    today = today or facility_today()
    existing = {(v.visit_type, v.due_date) for v in plan.visits}
    existing_dates = {v.due_date for v in plan.visits}
    created = []
    for pv in build_schedule(delivery_date, risk_flags):
        if (pv.visit_type, pv.due_date) in existing or pv.due_date in existing_dates:
            continue
        visit = PostnatalVisit(
            visit_type=pv.visit_type,
            due_date=pv.due_date,
            status=status_for(pv.due_date, today),
        )
        plan.visits.append(visit)
        created.append(visit)
    db.flush()
    return created


def recompute_all_visit_statuses(db: Session, current_date: date | None = None, facility_id: int | None = None) -> int:
    """FR-005: refresh Upcoming / Due today / Overdue for every open visit on an active plan."""
    current_date = current_date or facility_today()
    query = (
        db.query(PostnatalVisit)
        .join(DischargePlan)
        .filter(
            DischargePlan.status == DischargePlanStatus.ACTIVE.value,
            PostnatalVisit.status.in_(OPEN_VISIT_STATUSES),
        )
    )
    if facility_id is not None:
        query = query.join(Patient, DischargePlan.patient_id == Patient.patient_id).filter(
            Patient.facility_id == facility_id
        )

    updated = 0
    for visit in query.all():
        new_status = status_for(visit.due_date, current_date)
        if visit.status != new_status:
            visit.status = new_status
            updated += 1
    db.flush()
    return updated


def refresh_facility_statuses(db: Session, facility_id: int, today: date | None = None) -> int:
    """Brings one facility's visit statuses up to date before they're read, so a
    late or skipped daily job never shows yesterday's due/overdue state."""
    today = today or facility_today()
    updated = recompute_all_visit_statuses(db, today, facility_id=facility_id)
    if updated:
        audit.record(
            db,
            action="RECOMPUTE_VISIT_STATUSES",
            entity="PostnatalVisit",
            facility_id=facility_id,
            details=f"{updated} visit statuses refreshed for {today.isoformat()}",
        )
        db.commit()
    return updated


def days_overdue(due_date: date, today: date | None = None) -> int:
    today = today or facility_today()
    return max((today - due_date).days, 0)
