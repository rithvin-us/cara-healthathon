from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.models import FamilyMember, ConsentRecord, Patient, AuditLog, StaffUser
from app.schemas.schemas import FamilyMemberCreate, FamilyMemberOut, ConsentUpdateRequest
from app.core.security import get_current_user, require_role
from app.core.config import settings
from app.services.nudge_engine import NudgeEngine

router = APIRouter(prefix=f"{settings.API_V1_STR}", tags=["family"])

@router.post("/patients/{patient_id}/family-members", response_model=FamilyMemberOut, status_code=status.HTTP_201_CREATED)
def add_family_member(
    patient_id: int,
    req: FamilyMemberCreate,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role(["Coordinator", "Doctor", "Admin"]))
):
    """
    FR-016: Coordinator adds a family member's contact for opt-in nudges with consent capture.
    """
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    fm = FamilyMember(
        patient_id=patient_id,
        name=req.name,
        relation=req.relation,
        contact_number=req.contact_number,
        preferred_language=req.preferred_language or "English"
    )
    db.add(fm)
    db.commit()
    db.refresh(fm)

    consent = ConsentRecord(
        family_id=fm.family_id,
        consent_given=req.consent_given,
        recorded_by=current_user.user_id,
        timestamp=datetime.utcnow()
    )
    db.add(consent)
    db.commit()

    audit = AuditLog(
        actor_id=current_user.user_id,
        action="ADD_FAMILY_CONSENT",
        entity="FamilyMember",
        entity_id=fm.family_id,
        details=f"Added family member {fm.name} ({fm.relation}) with consent={req.consent_given}"
    )
    db.add(audit)
    db.commit()

    return FamilyMemberOut(
        family_id=fm.family_id,
        patient_id=fm.patient_id,
        name=fm.name,
        relation=fm.relation,
        contact_number=fm.contact_number,
        preferred_language=fm.preferred_language,
        latest_consent=req.consent_given
    )


@router.patch("/family-members/{family_id}/consent", response_model=FamilyMemberOut)
def update_family_consent(
    family_id: int,
    req: ConsentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: StaffUser = Depends(require_role(["Coordinator", "Doctor", "Admin"]))
):
    """
    FR-017: Mother or coordinator revokes/grants a family member's access at any time.
    Nudges stop immediately if consent is revoked.
    """
    fm = db.query(FamilyMember).filter(FamilyMember.family_id == family_id).first()
    if not fm:
        raise HTTPException(status_code=404, detail="Family member not found")

    consent = ConsentRecord(
        family_id=family_id,
        consent_given=req.consent_given,
        recorded_by=current_user.user_id,
        timestamp=datetime.utcnow()
    )
    db.add(consent)
    db.commit()

    action_str = "GRANT_CONSENT" if req.consent_given else "REVOKE_CONSENT"
    audit = AuditLog(
        actor_id=current_user.user_id,
        action=action_str,
        entity="ConsentRecord",
        entity_id=consent.consent_id,
        details=f"Consent updated to {req.consent_given} for family member {fm.name}"
    )
    db.add(audit)
    db.commit()

    return FamilyMemberOut(
        family_id=fm.family_id,
        patient_id=fm.patient_id,
        name=fm.name,
        relation=fm.relation,
        contact_number=fm.contact_number,
        preferred_language=fm.preferred_language,
        latest_consent=req.consent_given
    )
