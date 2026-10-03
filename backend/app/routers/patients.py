from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.access import get_active_plan_or_404, get_patient_or_404, latest_plan
from app.core.clock import facility_today, utcnow
from app.core.config import settings
from app.core.security import get_current_user, require_role
from app.database import get_db
from app.models.models import (
    DischargePlan,
    DischargePlanStatus,
    Newborn,
    NudgeLog,
    Patient,
    RiskFlag,
    StaffRole,
    StaffUser,
)
from app.schemas.schemas import (
    ClosePlanRequest,
    DischargePlanOut,
    FamilyMemberOut,
    NewbornOut,
    NudgeLogOut,
    PatientCreate,
    PatientDetailOut,
    PatientOut,
    RiskFlagCreate,
    ScheduledVisit,
    SchedulePreviewOut,
    SchedulePreviewRequest,
)
from app.services import audit, calendar_engine, message_templates
from app.services.content_filter import ContentFilter

router = APIRouter(prefix=f"{settings.API_V1_STR}", tags=["patients"])

DOCTOR_OR_ADMIN = require_role([StaffRole.DOCTOR, StaffRole.ADMIN])
CARE_TEAM = require_role([StaffRole.DOCTOR, StaffRole.COORDINATOR, StaffRole.ADMIN])


def build_patient_detail(db: Session, patient: Patient) -> PatientDetailOut:
    plan = latest_plan(patient)

    family_out = []
    for member in patient.family_members:
        latest = member.consent_records[-1] if member.consent_records else None
        family_out.append(
            FamilyMemberOut(
                family_id=member.family_id,
                patient_id=member.patient_id,
                name=member.name,
                relation=member.relation,
                contact_number=member.contact_number,
                preferred_language=member.preferred_language,
                latest_consent=bool(latest and latest.consent_given),
                consent_updated_at=latest.timestamp if latest else None,
            )
        )

    nudges = []
    if plan and plan.visits:
        nudges = (
            db.query(NudgeLog)
            .filter(NudgeLog.visit_id.in_([v.visit_id for v in plan.visits]))
            .order_by(NudgeLog.sent_at.desc(), NudgeLog.nudge_id.desc())
            .all()
        )

    return PatientDetailOut(
        patient=PatientOut.model_validate(patient),
        newborns=[NewbornOut.model_validate(n) for n in patient.newborns],
        active_plan=DischargePlanOut.model_validate(plan) if plan else None,
        family_members=family_out,
        nudges=[NudgeLogOut.model_validate(n) for n in nudges],
    )


@router.post("/schedule/preview", response_model=SchedulePreviewOut)
def preview_schedule(req: SchedulePreviewRequest, _: StaffUser = Depends(get_current_user)):
    """Returns the exact visit schedule a discharge plan would create (FR-001/FR-002)."""
    planned = calendar_engine.build_schedule(req.delivery_date, req.risk_flags)
    return SchedulePreviewOut(
        risk_tier=calendar_engine.risk_tier(req.risk_flags),
        visits=[
            ScheduledVisit(visit_type=p.visit_type, due_date=p.due_date, is_risk_visit=p.is_risk_visit) for p in planned
        ],
    )


@router.post("/patients", response_model=PatientDetailOut, status_code=status.HTTP_201_CREATED)
def create_patient_and_discharge_plan(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(DOCTOR_OR_ADMIN),
):
    """FR-001: create the mother, baby and discharge plan, and schedule the WHO
    default visits plus any FOGSI risk-based extra visits (FR-002), in one transaction."""
    today = facility_today()
    if patient_in.delivery_date > today:
        raise HTTPException(status_code=422, detail="Delivery date can't be in the future.")
    if patient_in.discharge_date < patient_in.delivery_date:
        raise HTTPException(status_code=422, detail="Discharge date can't be before the delivery date.")
    if patient_in.discharge_date > today:
        raise HTTPException(status_code=422, detail="Discharge date can't be in the future.")

    duplicate = (
        db.query(Patient)
        .filter(Patient.facility_id == current_user.facility_id, Patient.contact_number == patient_in.contact_number)
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A mother with this phone number is already registered ({duplicate.name}).",
        )

    risk_flags = list(dict.fromkeys(f.value for f in patient_in.risk_flags))

    patient = Patient(
        facility_id=current_user.facility_id,
        name=patient_in.name,
        contact_number=patient_in.contact_number,
        preferred_language=patient_in.preferred_language,
        delivery_date=patient_in.delivery_date,
        discharge_date=patient_in.discharge_date,
    )
    patient.newborns.append(
        Newborn(dob=patient_in.delivery_date, gender=patient_in.newborn_gender, name_or_initial=patient_in.newborn_name)
    )
    plan = DischargePlan(created_by=current_user.user_id, status=DischargePlanStatus.ACTIVE.value)
    plan.risk_flags = [RiskFlag(flag_type=f) for f in risk_flags]
    patient.discharge_plans.append(plan)
    db.add(patient)
    db.flush()

    visits = calendar_engine.create_plan_visits(db, plan, patient.delivery_date, risk_flags, today=today)
    audit.record(
        db,
        actor=current_user,
        action="CREATE_DISCHARGE_PLAN",
        entity="DischargePlan",
        entity_id=plan.plan_id,
        patient_id=patient.patient_id,
        details=(
            f"Discharge plan for {patient.name} with {len(visits)} visits"
            + (f"; risk: {message_templates.describe_risks(risk_flags)}" if risk_flags else "")
        ),
    )
    db.commit()
    db.refresh(patient)
    return build_patient_detail(db, patient)


@router.get("/patients/{patient_id}", response_model=PatientDetailOut)
def get_patient_detail(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    """FR-010 / FR-018: full visit history, consent status and reminder log."""
    patient = get_patient_or_404(db, patient_id, current_user)
    calendar_engine.refresh_facility_statuses(db, current_user.facility_id)
    return build_patient_detail(db, patient)


@router.post("/patients/{patient_id}/risk-flags", response_model=DischargePlanOut)
def apply_risk_flag_override(
    patient_id: int,
    risk_in: RiskFlagCreate,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role([StaffRole.DOCTOR])),
):
    """FR-002: flag a risk condition after discharge. Extra visits are added for
    the new cadence; completed visits and reminder history are never touched."""
    patient = get_patient_or_404(db, patient_id, current_user)
    plan = get_active_plan_or_404(patient)

    flag = risk_in.flag_type.value
    if flag in {rf.flag_type for rf in plan.risk_flags}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This risk flag is already on her plan.")

    plan.risk_flags.append(RiskFlag(flag_type=flag))
    db.flush()
    added = calendar_engine.create_plan_visits(
        db, plan, patient.delivery_date, [rf.flag_type for rf in plan.risk_flags]
    )
    audit.record(
        db,
        actor=current_user,
        action="APPLY_RISK_FLAG",
        entity="DischargePlan",
        entity_id=plan.plan_id,
        patient_id=patient.patient_id,
        details=f"Risk flag added ({message_templates.describe_risks([flag])}); {len(added)} extra visits scheduled",
    )
    db.commit()
    db.refresh(plan)
    return DischargePlanOut.model_validate(plan)


@router.post("/patients/{patient_id}/plan/close", response_model=DischargePlanOut)
def close_discharge_plan(
    patient_id: int,
    req: ClosePlanRequest,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(CARE_TEAM),
):
    """FR-004: close a plan once follow-up is finished or care moves elsewhere.
    Closed plans drop off the worklist and get no further reminders."""
    patient = get_patient_or_404(db, patient_id, current_user)
    plan = get_active_plan_or_404(patient)
    is_valid, reason = ContentFilter.inspect_text(req.reason)
    if not is_valid:
        raise HTTPException(status_code=422, detail=f"Keep the reason non-clinical. {reason}")
    plan.status = DischargePlanStatus.CLOSED.value
    plan.closed_at = utcnow()
    plan.closed_reason = req.reason
    audit.record(
        db,
        actor=current_user,
        action="CLOSE_DISCHARGE_PLAN",
        entity="DischargePlan",
        entity_id=plan.plan_id,
        patient_id=patient.patient_id,
        details=f"Plan closed: {req.reason}",
    )
    db.commit()
    db.refresh(plan)
    return DischargePlanOut.model_validate(plan)
