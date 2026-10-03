import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from app.core.clock import facility_today
from app.core.config import settings
from app.core.security import require_role
from app.database import get_db
from app.models.models import DischargePlan, Patient, PostnatalVisit, StaffRole, StaffUser, VisitStatus
from app.schemas.schemas import OutcomesReportOut, VisitTypeOutcome
from app.services import audit
from app.services.calendar_engine import refresh_facility_statuses

router = APIRouter(prefix=f"{settings.API_V1_STR}/reports", tags=["reports"])

# Order rows the way the schedule runs, not alphabetically.
_VISIT_ORDER = [
    "24h Checkup",
    "48-72h Checkup",
    "Weekly Risk Checkup (Week 1)",
    "7-14d Checkup",
    "Weekly Risk Checkup (Week 2)",
    "Post-op/Anemia Checkup (Week 2)",
    "Specialist Follow-Up",
    "Weekly Risk Checkup (Week 3)",
    "Weekly Risk Checkup (Week 4)",
    "Post-op/Anemia Checkup (Week 4)",
    "6wk Checkup",
]


def _rate(done: int, total: int) -> float:
    return round(done / total * 100, 1) if total else 0.0


@router.get("/outcomes", response_model=OutcomesReportOut)
def generate_outcomes_report(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    export: str | None = Query(None, pattern="^csv$"),
    anonymize: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role([StaffRole.DOCTOR, StaffRole.ADMIN])),
):
    """FR-019: due-vs-completed report by visit type, over visits due on or before
    today (and within the date range). FR-020: `export=csv&anonymize=true` strips
    names and phone numbers for external sharing."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="The start date must be on or before the end date.")
    if export == "csv" and not anonymize and current_user.role != StaffRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Only a facility admin can export names. Tick 'Anonymise'.")

    refresh_facility_statuses(db, current_user.facility_id)

    query = (
        db.query(PostnatalVisit)
        .join(DischargePlan)
        .join(Patient, DischargePlan.patient_id == Patient.patient_id)
        .filter(Patient.facility_id == current_user.facility_id)
        .options(joinedload(PostnatalVisit.plan).joinedload(DischargePlan.patient))
    )
    # Due-vs-completed: only visits that have fallen due count; future visits
    # would drag the completion rate down for reasons nobody can act on yet.
    today = facility_today()
    cutoff = min(end_date, today) if end_date else today
    query = query.filter(PostnatalVisit.due_date <= cutoff)
    if start_date:
        query = query.filter(PostnatalVisit.due_date >= start_date)
    visits = query.order_by(PostnatalVisit.due_date, PostnatalVisit.visit_id).all()

    if export == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        if anonymize:
            writer.writerow(["visit_ref", "visit_type", "due_date", "status", "completed_date"])
            for i, v in enumerate(visits, start=1):
                writer.writerow([f"V{i:04d}", v.visit_type, v.due_date, v.status, v.completed_date or ""])
        else:
            writer.writerow(
                ["visit_id", "patient_name", "contact_number", "visit_type", "due_date", "status", "completed_date"]
            )
            for v in visits:
                p = v.plan.patient
                writer.writerow(
                    [v.visit_id, p.name, p.contact_number, v.visit_type, v.due_date, v.status, v.completed_date or ""]
                )
        audit.record(
            db,
            actor=current_user,
            action="EXPORT_REPORT",
            entity="Report",
            details=f"{'Anonymised' if anonymize else 'Identified'} CSV export of {len(visits)} visits",
        )
        db.commit()
        filename = "cara_outcomes_anonymised.csv" if anonymize else "cara_outcomes_report.csv"
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    by_type: dict[str, dict[str, int]] = {}
    for v in visits:
        counts = by_type.setdefault(v.visit_type, {"total": 0, "completed": 0, "missed": 0, "overdue": 0})
        counts["total"] += 1
        if v.status in counts:
            counts[v.status] += 1

    order = {name: i for i, name in enumerate(_VISIT_ORDER)}
    outcomes = [
        VisitTypeOutcome(
            visit_type=vt,
            total=c["total"],
            completed=c["completed"],
            missed=c["missed"],
            overdue=c["overdue"],
            completion_rate_pct=_rate(c["completed"], c["total"]),
        )
        for vt, c in sorted(by_type.items(), key=lambda kv: order.get(kv[0], len(order)))
    ]

    completed = sum(1 for v in visits if v.status == VisitStatus.COMPLETED.value)
    return OutcomesReportOut(
        start_date=start_date,
        end_date=end_date,
        total_patients=len({v.plan.patient_id for v in visits}),
        total_visits=len(visits),
        completed_visits=completed,
        missed_visits=sum(1 for v in visits if v.status == VisitStatus.MISSED.value),
        overdue_visits=sum(1 for v in visits if v.status == VisitStatus.OVERDUE.value),
        overall_completion_rate_pct=_rate(completed, len(visits)),
        outcomes_by_visit_type=outcomes,
    )
