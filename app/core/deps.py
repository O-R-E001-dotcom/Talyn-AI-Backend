"""FastAPI dependencies: current user from JWT bearer token."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Enrollment, User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from app.core.security import decode_token

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload["sub"])
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Restrict an endpoint to admin users (course management, etc.)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_creator(
    current_user: User = Depends(get_current_user),
) -> User:
    """Restrict an endpoint to creators (admins pass through)."""
    if not (current_user.is_creator or current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Creator access required",
        )
    return current_user


def can_manage_course(course, user: User) -> bool:
    """Owners manage their own courses; admins manage everything."""
    return user.is_admin or (
        course.creator_user_id is not None and course.creator_user_id == user.id
    )


def can_read_content(db: Session, viewer: User | None, course) -> bool:
    """Paid content needs a purchase enrollment; free content is public.

    Drafts/archived are manager-only. Direct (non-purchase) enrollments
    cover preview/audit, not paid content access.
    """
    from app.models.course import STATUS_PUBLISHED

    if course.status != STATUS_PUBLISHED:
        return viewer is not None and can_manage_course(course, viewer)
    if course.course_type == "free":
        return True
    if viewer is None or can_manage_course(course, viewer):
        return viewer is not None
    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.user_id == viewer.id,
            Enrollment.course_id == course.id,
        )
    )
    return enrollment is not None and enrollment.source == "purchase"


_optional_bearer = HTTPBearer(auto_error=False)


def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """Best-effort auth for public endpoints: None when anonymous/invalid."""
    if credentials is None:
        return None
    from app.core.security import decode_token

    payload = decode_token(credentials.credentials)
    if payload is None:
        return None
    try:
        return db.get(User, int(payload["sub"]))
    except (KeyError, TypeError, ValueError):
        return None