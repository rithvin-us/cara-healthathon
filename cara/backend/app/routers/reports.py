from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
import io
import csv

from app.database import get_db
from app.models.models import PostnatalVisit, Patient, VisitStatus, StaffUser
from app.schemas.schemas import OutcomesReportOut, VisitTypeOutcome
from app.core.security import get_current_user, require_role
from app.core.config import settings

router = APIRouter(prefix=f"{settings.API_V1_STR}/reports", tags=["reports"])

@router.get("/outcomes")
def generate_outcomes_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    export: Optional[str] = Query(None), # "csv"
    anonymize: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role(["Doctor", "Admin"]))
):
    """
    FR-019: Generate Due-vs-Completed Report & FR-020: Export Anonymised Summary.
    """
    query = db.query(PostnatalVisit).join(PostnatalVisit.plan).join(Patient).filter(
        Patient.facility_id == current_user.facility_id
    )

    if start_date:
        query = query.filter(PostnatalVisit.due_date >= start_date)
    if end_date:
        query = query.filter(PostnatalVisit.due_date <= end_date)

    visits = query.all()

    total_visits = len(visits)
    completed_visits = sum(1 for v in visits if v.status == VisitStatus.COMPLETED.value)
    missed_visits = sum(1 for v in visits if v.status == VisitStatus.MISSED.value)
    overdue_visits = sum(1 for v in visits if v.status == VisitStatus.OVERDUE.value)
    overall_rate = round((completed_visits / total_visits * 100), 1) if total_visits > 0 else 0.0

    # Group by visit type
    by_type = {}
    for v in visits:
        v_type = v.visit_type
        if v_type not in by_type:
            by_type[v_type] = {"total": 0, "completed": 0, "missed": 0, "overdue": 0}
        by_type[v_type]["total"] += 1
        if v.status == VisitStatus.COMPLETED.value:
            by_type[v_type]["completed"] += 1
        elif v.status == VisitStatus.MISSED.value:
            by_type[v_type]["missed"] += 1
        elif v.status == VisitStatus.OVERDUE.value:
            by_type[v_type]["overdue"] += 1

    visit_outcomes = []
    for vt, counts in by_type.items():
        tot = counts["total"]
        comp = counts["completed"]
        rate = round((comp / tot * 100), 1) if tot > 0 else 0.0
        visit_outcomes.append(
            VisitTypeOutcome(
                visit_type=vt,
                total=tot,
                completed=comp,
                missed=counts["missed"],
                overdue=counts["overdue"],
                completion_rate_pct=rate
            )
        )

    # Unique patients
    patient_ids = set(v.plan.patient_id for v in visits)
    total_patients = len(patient_ids)

    if export == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        if anonymize:
            writer.writerow(["Visit ID", "Visit Type", "Due Date", "Status", "Completion Date"])
            for v in visits:
                writer.writerow([v.visit_id, v.visit_type, v.due_date, v.status, v.completed_date or ""])
        else:
            writer.writerow(["Visit ID", "Patient Name", "Visit Type", "Due Date", "Status", "Completion Date"])
            for v in visits:
                writer.writerow([v.visit_id, v.plan.patient.name, v.visit_type, v.due_date, v.status, v.completed_date or ""])
        
        output.seek(0)
        filename = "cara_anonymised_outcomes.csv" if anonymize else "cara_outcomes_report.csv"
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    return OutcomesReportOut(
        start_date=start_date or date(2026, 1, 1),
        end_date=end_date or date(2026, 12, 31),
        total_patients=total_patients,
        total_visits=total_visits,
        completed_visits=completed_visits,
        missed_visits=missed_visits,
        overdue_visits=overdue_visits,
        overall_completion_rate_pct=overall_rate,
        outcomes_by_visit_type=visit_outcomes
    )
