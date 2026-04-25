from sqlalchemy.orm import Session
from app.models.user import User
from app.audit.audit_services import create_audit_log
from fastapi import HTTPException, Request, status


def get_all_users(db: Session):
    """
    Fetch all users from database
    """
    return db.query(User).all()


def update_user(
    *,
    user_id: str,
    user_data,
    db: Session,
    current_user,
    request: Request
):
    """
    Update username/email and create detailed audit log
    """

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

   
    old_username = user.username
    old_email = user.email

   
    if user_data.username is not None:
        user.username = user_data.username

    if user_data.email is not None:
        user.email = user_data.email

    db.commit()
    db.refresh(user)
    changes = []

    if old_username != user.username:
        changes.append(
            f"username changed from '{old_username}' to '{user.username}'"
        )

    if old_email != user.email:
        changes.append(
            f"email changed from '{old_email}' to '{user.email}'"
        )

    description = (
        f"Updated user {user.id}: " + ", ".join(changes)
        if changes else
        f"Update attempted on user {user.id}, no changes applied"
    )

    create_audit_log(
        db=db,
        log_type="USER",
        user_id=current_user.id if current_user else None,
        username=current_user.username if current_user else None,
        module="User",
        action="UPDATE",
        resource_type="User",
        resource_id=str(user.id),
        status="success",
        remote_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        description=description
    )

    return user