"""Facility-scoped lookups.

Every record is reached through the signed-in user's facility. A record from
another facility returns 404 rather than 403 so IDs can't be probed.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import (
    DischargePlan,
    DischargePlanStatus,
    FamilyMember,
    Patient,
    PostnatalVisit,
    StaffUser,
)


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found")


def get_patient_or_404(db: Session, patient_id: int, user: StaffUser) -> Patient:
    patient = (
        db.query(Patient).filter(Patient.patient_id == patient_id, Patient.facility_id == user.facility_id).first()
    )
    if not patient:
        raise _not_found("Patient")
    return patient


def get_visit_or_404(db: Session, visit_id: int, user: StaffUser) -> PostnatalVisit:
    visit = (
        db.query(PostnatalVisit)
        .join(DischargePlan)
        .join(Patient, DischargePlan.patient_id == Patient.patient_id)
        .filter(PostnatalVisit.visit_id == visit_id, Patient.facility_id == user.facility_id)
        .first()
    )
    if not visit:
        raise _not_found("Visit")
    return visit


def get_family_member_or_404(db: Session, family_id: int, user: StaffUser) -> FamilyMember:
    member = (
        db.query(FamilyMember)
        .join(Patient)
        .filter(FamilyMember.family_id == family_id, Patient.facility_id == user.facility_id)
        .first()
    )
    if not member:
        raise _not_found("Family member")
    return member


def latest_plan(patient: Patient) -> DischargePlan | None:
    return patient.discharge_plans[-1] if patient.discharge_plans else None


def get_active_plan_or_404(patient: Patient) -> DischargePlan:
    plan = latest_plan(patient)
    if not plan or plan.status != DischargePlanStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This mother has no active discharge plan.")
    return plan
