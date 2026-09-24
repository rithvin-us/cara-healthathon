from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models.models import PostnatalVisit, DischargePlan, Patient, RiskFlag, StaffUser, VisitStatus
from app.schemas.schemas import WorklistItem
from app.core.security import get_current_user
from app.core.config import settings

router = APIRouter(prefix=f"{settings.API_V1_STR}/worklist", tags=["worklist"])

@router.get("", response_model=List[WorklistItem])
def get_ranked_worklist(
    visit_type: Optional[str] = Query(None),
    risk_flag: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user)
):
    """
    FR-008: Coordinator sees all active patients at their facility sorted by days-overdue descending.
    FR-009: Filter worklist by visit type or risk flag.
    """
    query = db.query(PostnatalVisit).join(DischargePlan).join(Patient).filter(
        Patient.facility_id == current_user.facility_id,
        DischargePlan.status == "active",
        PostnatalVisit.status.in_([VisitStatus.OVERDUE.value, VisitStatus.DUE_TODAY.value])
    )

    if visit_type:
        query = query.filter(PostnatalVisit.visit_type == visit_type)

    if risk_flag:
        query = query.filter(DischargePlan.risk_flags.any(RiskFlag.flag_type == risk_flag))

    visits = query.all()
    today = date.today()

    worklist_items = []
    for visit in visits:
        patient = visit.plan.patient
        days_ovd = (today - visit.due_date).days if visit.due_date < today else 0
        r_flags = [rf.flag_type for rf in visit.plan.risk_flags]

        worklist_items.append(
            WorklistItem(
                patient_id=patient.patient_id,
                patient_name=patient.name,
                contact_number=patient.contact_number,
                preferred_language=patient.preferred_language,
                visit_id=visit.visit_id,
                visit_type=visit.visit_type,
                due_date=visit.due_date,
                days_overdue=days_ovd,
                status=visit.status,
                risk_flags=r_flags
            )
        )

    # Sort by days_overdue descending, then due_date ascending
    worklist_items.sort(key=lambda item: item.days_overdue, reverse=True)
    return worklist_items
