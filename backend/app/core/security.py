from datetime import timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.config import settings
from app.database import get_db
from app.models.models import StaffRole, StaffUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

# bcrypt only looks at the first 72 bytes of a password.
_BCRYPT_MAX_BYTES = 72


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES],
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        # Malformed hash in the database: treat as a failed login, never fall back
        # to comparing plaintext.
        return False


def get_password_hash(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8")[:_BCRYPT_MAX_BYTES], bcrypt.gensalt())
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)


def token_for_user(user: StaffUser) -> str:
    return create_access_token(
        {
            "sub": user.email,
            "user_id": user.user_id,
            "role": user.role,
            "facility_id": user.facility_id,
        }
    )


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> StaffUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Your session has expired. Please sign in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        raise credentials_exception from None

    user_id = payload.get("user_id")
    if payload.get("sub") is None or user_id is None:
        raise credentials_exception

    user = db.get(StaffUser, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(allowed_roles: list[StaffRole | str]):
    allowed = {r.value if isinstance(r, StaffRole) else r for r in allowed_roles}

    def role_checker(current_user: StaffUser = Depends(get_current_user)) -> StaffUser:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your role doesn't have permission for this action.",
            )
        return current_user

    return role_checker
