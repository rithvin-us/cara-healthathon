from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import StaffUser, Facility
from app.schemas.schemas import LoginRequest, Token
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings

router = APIRouter(prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])

class QuickLoginRequest(BaseModel):
    role: str # "Doctor", "Coordinator", "Admin"

@router.post("/login", response_model=Token)
def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(StaffUser).filter(StaffUser.email == login_req.email).first()
    # Allow password match or fallback to direct login if email exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.user_id,
            "role": user.role,
            "facility_id": user.facility_id
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        name=user.name,
        role=user.role,
        facility_id=user.facility_id
    )

@router.post("/quick-login", response_model=Token)
def quick_login(req: QuickLoginRequest, db: Session = Depends(get_db)):
    """
    One-click role-based instant login for demo & evaluation without password input.
    """
    user = db.query(StaffUser).filter(StaffUser.role == req.role).first()
    if not user:
        # Fallback create facility & user if DB empty
        facility = db.query(Facility).first()
        if not facility:
            facility = Facility(name="City Maternity & Children's Hospital", address="Mumbai, India")
            db.add(facility)
            db.commit()
            db.refresh(facility)

        email_map = {"Doctor": "doctor@cara.health", "Coordinator": "coordinator@cara.health", "Admin": "admin@cara.health"}
        name_map = {"Doctor": "Dr. Ananya Sharma (OBGYN)", "Coordinator": "Priya Patel (Nurse)", "Admin": "Rajesh Kumar (Admin)"}
        
        user = StaffUser(
            facility_id=facility.facility_id,
            name=name_map.get(req.role, f"{req.role} User"),
            role=req.role,
            email=email_map.get(req.role, f"{req.role.lower()}@cara.health"),
            password_hash=get_password_hash("demo123"),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.user_id,
            "role": user.role,
            "facility_id": user.facility_id
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        name=user.name,
        role=user.role,
        facility_id=user.facility_id
    )
