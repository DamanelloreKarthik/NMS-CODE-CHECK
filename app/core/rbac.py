
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(default=None),
):
    """
    Temporary authentication:
    Reads user ID from request header: X-User-Id
    Replace with JWT later.
    """

    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication",
        )

    user = (
        db.query(User)
        .filter(User.id == x_user_id, User.is_active == True)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


def require_permission(permission: str):
    """
    Dependency to enforce RBAC permissions using DB users
    """

    def permission_checker(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        if not user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned",
            )

        role_permissions = {perm.name for perm in user.role.permissions}

        if permission not in role_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return user

    return permission_checker
