from collections.abc import Callable

from fastapi import Depends, Header, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppException
from app.core.security import decode_access_token
from app.db.models import User


def get_token_from_header(authorization: str | None = Header(None)) -> str:
    if not authorization:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHENTICATED",
            message="Missing authentication token.",
        )
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHENTICATED",
            message="Invalid Authorization header format. Expected 'Bearer <token>'.",
        )
    return parts[1]


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header),
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("Token missing 'sub' claim.")
    except Exception as err:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHENTICATED",
            message="Invalid, expired or tampered authentication token.",
        ) from err

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHENTICATED",
            message="User associated with token not found.",
        )
    return user


def require_role(allowed_roles: list[str]) -> Callable:
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            msg = f"Access forbidden: requires {allowed_roles}, role is {current_user.role}."
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message=msg,
            )
        return current_user

    return role_checker
