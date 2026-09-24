from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.database import get_db
from app.models.models import Patient, Newborn, DischargePlan, RiskFlag, PostnatalVisit, FamilyMember, ConsentRecord, AuditLog, StaffUser, NudgeLog
from app.schemas.schemas import PatientCreate, PatientOut, PatientDetailOut, DischargePlanOut, RiskFlagCreate, RiskFlagOut, FamilyMemberOut
from app.core.security import get_current_user, require_role
from app.core.config import settings
from app.services.calendar_engine import CalendarEngine
from app.services.nudge_engine import NudgeEngine

router = APIRouter(prefix=f"{settings.API_V1_STR}/patients", tags=["patients"])

@router.post("", response_model=PatientDetailOut, status_code=status.HTTP_201_CREATED)
def create_patient_and_discharge_plan(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role(["Doctor", "Admin"]))
):
    """
    FR-001: Doctor creates a postnatal follow-up plan for a newly discharged patient.
    Generates default WHO visit records or applies risk-based interval overrides (FR-002).
    """
    if not patient_in.contact_number or not patient_in.contact_number.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact number is required"
        )

    # Check duplicate patient contact in facility
    existing = db.query(Patient).filter(
        Patient.facility_id == current_user.facility_id,
        Patient.contact_number == patient_in.contact_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient with this contact already exists"
        )

    # 1. Create Patient
    patient = Patient(
        facility_id=current_user.facility_id,
        name=patient_in.name,
        contact_number=patient_in.contact_number,
        preferred_language=patient_in.preferred_language or "English",
        delivery_date=patient_in.delivery_date,
        discharge_date=patient_in.discharge_date
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    # 2. Create Newborn
    newborn = Newborn(
        patient_id=patient.patient_id,
        dob=patient_in.delivery_date,
        gender=patient_in.newborn_gender,
        name_or_initial=patient_in.newborn_name
    )
    db.add(newborn)

    # 3. Create Discharge Plan
    plan = DischargePlan(
        patient_id=patient.patient_id,
        created_by=current_user.user_id,
        status="active"
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    # 4. Add Risk Flags if provided (FR-002)
    risk_flags_list = patient_in.risk_flags or []
    for r_type in risk_flags_list:
        rf = RiskFlag(
            plan_id=plan.plan_id,
            flag_type=r_type
        )
        db.add(rf)

    db.commit()

    # 5. Generate Visit Records using Calendar Engine
    visits = CalendarEngine.create_plan_visits(db, plan.plan_id, patient_in.delivery_date, risk_flags_list)

    # 6. Audit Log Entry (FR-021)
    audit = AuditLog(
        actor_id=current_user.user_id,
        action="CREATE_DISCHARGE_PLAN",
        entity="DischargePlan",
        entity_id=plan.plan_id,
        details=f"Created discharge plan for patient {patient.name} with {len(visits)} visits"
    )
    db.add(audit)
    db.commit()

    return get_patient_detail(patient.patient_id, db=db, current_user=current_user)


@router.get("/{patient_id}", response_model=PatientDetailOut)
def get_patient_detail(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user)
):
    """
    FR-010: Patient Detail View. Full visit history, consent status, and nudge logs.
    """
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    plan = db.query(DischargePlan).filter(DischargePlan.patient_id == patient_id).order_by(DischargePlan.plan_id.desc()).first()

    family_members = db.query(FamilyMember).filter(FamilyMember.patient_id == patient_id).all()
    family_outs = []
    for fm in family_members:
        is_consent = NudgeEngine.is_family_consent_active(db, fm.family_id)
        family_outs.append(
            FamilyMemberOut(
                family_id=fm.family_id,
                patient_id=fm.patient_id,
                name=fm.name,
                relation=fm.relation,
                contact_number=fm.contact_number,
                preferred_language=fm.preferred_language,
                latest_consent=is_consent
            )
        )

    nudges = []
    if plan:
        visit_ids = [v.visit_id for v in plan.visits]
        if visit_ids:
            nudges = db.query(NudgeLog).filter(NudgeLog.visit_id.in_(visit_ids)).all()

    return PatientDetailOut(
        patient=PatientOut.model_validate(patient),
        active_plan=DischargePlanOut.model_validate(plan) if plan else None,
        family_members=family_outs,
        nudges=nudges
    )


@router.post("/{patient_id}/risk-flags", response_model=DischargePlanOut)
def apply_risk_flag_override(
    patient_id: int,
    risk_in: RiskFlagCreate,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role(["Doctor"]))
):
    """
    FR-002: Doctor flags a risk condition (e.g. hypertension).
    Re-generates or updates visit schedule to risk-based cadence.
    """
    plan = db.query(DischargePlan).filter(
        DischargePlan.patient_id == patient_id,
        DischargePlan.status == "active"
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Active discharge plan not found")

    patient = plan.patient

    # Add risk flag
    rf = RiskFlag(plan_id=plan.plan_id, flag_type=risk_in.flag_type)
    db.add(rf)
    db.commit()

    # Get all active risk flags
    all_flags = [f.flag_type for f in plan.risk_flags]

    # Delete existing non-completed visits to apply new cadence
    db.query(PostnatalVisit).filter(
        PostnatalVisit.plan_id == plan.plan_id,
        PostnatalVisit.status.in_(["upcoming", "due_today", "overdue"])
    ).delete(synchronize_session=False)
    db.commit()

    # Re-create plan visits with new risk flags
    CalendarEngine.create_plan_visits(db, plan.plan_id, patient.delivery_date, all_flags)

    # Audit Log
    audit = AuditLog(
        actor_id=current_user.user_id,
        action="APPLY_RISK_FLAG",
        entity="RiskFlag",
        entity_id=rf.flag_id,
        details=f"Applied risk flag {risk_in.flag_type} to plan #{plan.plan_id}"
    )
    db.add(audit)
    db.commit()

    db.refresh(plan)
    return DischargePlanOut.model_validate(plan)
