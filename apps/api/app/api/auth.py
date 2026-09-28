from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    digest_token,
    hash_password,
    new_refresh_token,
    verify_password,
)
from app.models.entities import AuditLog, RefreshToken, Role, RoleName, User
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest, TokenPair, UserRead


router = APIRouter(prefix="/auth", tags=["authentication"])


def _issue_pair(db: Session, user: User) -> TokenPair:
    settings = get_settings()
    raw_refresh, refresh_hash = new_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    db.commit()
    return TokenPair(
        access_token=create_access_token(user.id, user.role.name.value),
        refresh_token=raw_refresh,
        expires_in=settings.access_token_minutes * 60,
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> UserRead:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    settings = get_settings()
    user_count = db.scalar(select(func.count(User.id))) or 0
    role_name = (
        RoleName.ADMIN
        if user_count == 0 and settings.bootstrap_admin_email and email == settings.bootstrap_admin_email.lower()
        else RoleName.VIEWER
    )
    role = db.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        raise HTTPException(status_code=503, detail="Database roles are not initialized")
    user = User(email=email, password_hash=hash_password(payload.password), role_id=role.id)
    db.add(user)
    db.flush()
    db.add(AuditLog(user_id=user.id, action="USER_REGISTERED", source_ip=request.client.host if request.client else None))
    db.commit()
    db.refresh(user)
    return UserRead(id=user.id, email=user.email, role=user.role.name.value, is_active=user.is_active)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    db.add(AuditLog(user_id=user.id, action="USER_LOGIN", source_ip=request.client.host if request.client else None))
    db.commit()
    return _issue_pair(db, user)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == digest_token(payload.refresh_token)))
    now = datetime.now(UTC)
    if record is None or record.revoked_at is not None or record.expires_at.replace(tzinfo=UTC) <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    record.revoked_at = now
    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    db.commit()
    return _issue_pair(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> None:
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == digest_token(payload.refresh_token)))
    if record and record.revoked_at is None:
        record.revoked_at = datetime.now(UTC)
        db.commit()

