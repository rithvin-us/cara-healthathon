from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user, token_for_user, verify_password
from app.database import get_db
from app.models.models import Facility, StaffRole, StaffUser
from app.schemas.schemas import AuthConfigOut, DemoAccount, LoginRequest, QuickLoginRequest, StaffUserOut, Token

router = APIRouter(prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])

_INVALID_LOGIN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect email or password.",
    headers={"WWW-Authenticate": "Bearer"},
)

_ROLE_ORDER = {StaffRole.DOCTOR.value: 0, StaffRole.COORDINATOR.value: 1, StaffRole.ADMIN.value: 2}


def _token_response(db: Session, user: StaffUser) -> Token:
    facility = db.get(Facility, user.facility_id)
    return Token(
        access_token=token_for_user(user),
        user_id=user.user_id,
        name=user.name,
        role=user.role,
        facility_id=user.facility_id,
        facility_name=facility.name if facility else "",
    )


def _authenticate(db: Session, email: str, password: str) -> StaffUser:
    user = db.query(StaffUser).filter(StaffUser.email == email.lower()).first()
    if not user or not verify_password(password, user.password_hash):
        raise _INVALID_LOGIN
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been turned off.")
    return user


@router.post("/login", response_model=Token)
def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    """Email + password sign-in for staff."""
    return _token_response(db, _authenticate(db, login_req.email, login_req.password))


@router.post("/token", response_model=Token, include_in_schema=True)
def login_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 password flow, used by the Swagger UI "Authorize" button."""
    return _token_response(db, _authenticate(db, form.username, form.password))


@router.get("/config", response_model=AuthConfigOut)
def auth_config(db: Session = Depends(get_db)):
    """Tells the sign-in page whether one-click demo accounts are available."""
    if not settings.DEMO_MODE:
        return AuthConfigOut(demo_mode=False)
    facility = db.query(Facility).order_by(Facility.facility_id).first()
    users = (
        db.query(StaffUser)
        .filter(StaffUser.is_active.is_(True), StaffUser.facility_id == (facility.facility_id if facility else None))
        .all()
    )
    first_per_role: dict[str, StaffUser] = {}
    for user in sorted(users, key=lambda u: u.user_id):
        first_per_role.setdefault(user.role, user)
    accounts = [
        DemoAccount(role=u.role, name=u.name, email=u.email)
        for u in sorted(first_per_role.values(), key=lambda u: _ROLE_ORDER.get(u.role, 9))
    ]
    return AuthConfigOut(demo_mode=True, facility_name=facility.name if facility else None, demo_accounts=accounts)


@router.post("/quick-login", response_model=Token)
def quick_login(req: QuickLoginRequest, db: Session = Depends(get_db)):
    """One-click sign-in as the seeded demo account for a role. Only available
    when CARA_DEMO_MODE is on; never enable that with real patient data."""
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    user = (
        db.query(StaffUser)
        .filter(StaffUser.role == req.role.value, StaffUser.is_active.is_(True))
        .order_by(StaffUser.user_id)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active {req.role.value.lower()} account. Reset the demo data or sign in with email.",
        )
    return _token_response(db, user)


@router.get("/me", response_model=StaffUserOut)
def me(current_user: StaffUser = Depends(get_current_user)):
    return current_user
