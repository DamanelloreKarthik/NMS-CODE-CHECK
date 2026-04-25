
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import random

from app.core.security import get_password_hash
from app.core.database import get_db
from app.models.user import User
from app.users.user_schema import UserOut, UserUpdate, UserCreate
from app.audit.audit_services import create_audit_log
from app.models.refresh_token import RefreshToken

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/", response_model=UserOut)
def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
   
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    try:
       
        hashed_password = get_password_hash(user_data.password)

       
        user_code = f"USR{random.randint(1000,9999)}"

        new_user = User(
            user_code=user_code,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            username=user_data.username,
            email=user_data.email,
            mobile_number=user_data.mobile_number,
            password_hash=hashed_password,
            role_id=user_data.role_id,
            is_active=user_data.is_active
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        
        create_audit_log(
            db=db,
            module="USERS",
            action="CREATE",
            status="SUCCESS",
            description=f"User {new_user.username} created",
            request=request
        )

        return new_user

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/users/", response_model=list[UserOut])
def list_users(request: Request, db: Session = Depends(get_db)):

    users = db.query(User).all()

    current_username = getattr(request.state, "username", "SYSTEM")

    create_audit_log(
        db=db,
        module="USERS",
        action="GET_ALL",
        status="SUCCESS",
        description=f"{current_username} viewed all users",
        username=current_username,
        request=request
    )

    return users

@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = []

    if user_data.first_name and user_data.first_name != user.first_name:
        changes.append(f"first_name: {user.first_name} → {user_data.first_name}")
        user.first_name = user_data.first_name

    if user_data.last_name and user_data.last_name != user.last_name:
        changes.append(f"last_name: {user.last_name} → {user_data.last_name}")
        user.last_name = user_data.last_name

    if user_data.mobile_number and user_data.mobile_number != user.mobile_number:
        changes.append(f"mobile_number: {user.mobile_number} → {user_data.mobile_number}")
        user.mobile_number = user_data.mobile_number

    if user_data.username and user_data.username != user.username:
        changes.append(f"username: {user.username} → {user_data.username}")
        user.username = user_data.username

    if user_data.email and user_data.email != user.email:
        changes.append(f"email: {user.email} → {user_data.email}")
        user.email = user_data.email

    if user_data.role_id and user_data.role_id != user.role_id:
        changes.append("role_id changed")
        user.role_id = user_data.role_id

    if user_data.is_active is not None and user_data.is_active != user.is_active:
        changes.append(f"is_active: {user.is_active} → {user_data.is_active}")
        user.is_active = user_data.is_active

    if not changes:
        raise HTTPException(status_code=400, detail="No changes detected")

    try:
        create_audit_log(
            db=db,
            module="USERS",
            username=user.username,
            action="UPDATE",
            status="SUCCESS",
            description="; ".join(changes),
            request=request
        )

        db.commit()
        db.refresh(user)

        return user

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))



@router.delete("/{user_id}")
def delete_user(
    user_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
     
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id
        ).delete(synchronize_session=False)

        db.delete(user)

        create_audit_log(
            db=db,
            module="USERS",
            username=user.username,
            action="DELETE",
            status="SUCCESS",
            description=f"User {user.username} deleted",
            request=request
        )

        db.commit()

        return {"detail": "User deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


