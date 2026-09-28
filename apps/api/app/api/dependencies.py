import hmac
from collections.abc import Callable

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.entities import RoleName, User


bearer = HTTPBearer(auto_error=False)


def verify_sensor_key(x_sensor_key: str | None = Header(default=None)) -> None:
    expected = get_settings().sensor_api_key.get_secret_value()
    if not x_sensor_key or not hmac.compare_digest(x_sensor_key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid sensor credentials")


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc
    user = db.scalar(select(User).where(User.id == payload.get("sub")))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or unknown user")
    return user


def require_roles(*roles: RoleName) -> Callable[[User], User]:
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role.name not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dependency

