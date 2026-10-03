from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.access import get_family_member_or_404, get_patient_or_404
from app.core.config import settings
from app.core.security import require_role
from app.database import get_db
from app.models.models import ConsentRecord, FamilyMember, StaffRole, StaffUser
from app.schemas.schemas import ConsentUpdateRequest, FamilyMemberCreate, FamilyMemberOut
from app.services import audit

router = APIRouter(prefix=f"{settings.API_V1_STR}", tags=["family"])

CARE_TEAM = require_role([StaffRole.COORDINATOR, StaffRole.DOCTOR, StaffRole.ADMIN])


def _out(member: FamilyMember, consent: ConsentRecord) -> FamilyMemberOut:
    return FamilyMemberOut(
        family_id=member.family_id,
        patient_id=member.patient_id,
        name=member.name,
        relation=member.relation,
        contact_number=member.contact_number,
        preferred_language=member.preferred_language,
        latest_consent=consent.consent_given,
        consent_updated_at=consent.timestamp,
    )


@router.post(
    "/patients/{patient_id}/family-members", response_model=FamilyMemberOut, status_code=status.HTTP_201_CREATED
)
def add_family_member(
    patient_id: int,
    req: FamilyMemberCreate,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(CARE_TEAM),
):
    """FR-016: add a relative who may receive reminders, recording the mother's consent."""
    patient = get_patient_or_404(db, patient_id, current_user)
    if req.contact_number == patient.contact_number:
        raise HTTPException(status_code=422, detail="That's the mother's own number.")
    if any(m.contact_number == req.contact_number for m in patient.family_members):
        raise HTTPException(status_code=409, detail="This number is already on her family list.")

    member = FamilyMember(
        patient_id=patient.patient_id,
        name=req.name,
        relation=req.relation,
        contact_number=req.contact_number,
        preferred_language=req.preferred_language or patient.preferred_language,
    )
    db.add(member)
    db.flush()
    consent = ConsentRecord(
        family_id=member.family_id, consent_given=req.consent_given, recorded_by=current_user.user_id
    )
    db.add(consent)
    audit.record(
        db,
        actor=current_user,
        action="ADD_FAMILY_CONSENT",
        entity="FamilyMember",
        entity_id=member.family_id,
        patient_id=patient.patient_id,
        details=f"Added {member.name} ({member.relation}); consent {'given' if req.consent_given else 'not given'}",
    )
    db.commit()
    db.refresh(consent)
    return _out(member, consent)


@router.patch("/family-members/{family_id}/consent", response_model=FamilyMemberOut)
def update_family_consent(
    family_id: int,
    req: ConsentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(CARE_TEAM),
):
    """FR-017: grant or withdraw consent. A withdrawal stops the very next reminder."""
    member = get_family_member_or_404(db, family_id, current_user)
    consent = ConsentRecord(
        family_id=member.family_id, consent_given=req.consent_given, recorded_by=current_user.user_id
    )
    db.add(consent)
    db.flush()
    audit.record(
        db,
        actor=current_user,
        action="GRANT_CONSENT" if req.consent_given else "REVOKE_CONSENT",
        entity="ConsentRecord",
        entity_id=consent.consent_id,
        patient_id=member.patient_id,
        details=f"Consent {'given' if req.consent_given else 'withdrawn'} for {member.name} ({member.relation})",
    )
    db.commit()
    db.refresh(consent)
    return _out(member, consent)
