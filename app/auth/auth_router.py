
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from app.auth.auth_schemas import LoginRequest, RegisterRequest
from app.auth.auth_services import authenticate_user
from app.models.user import User, Role
from app.models.refresh_token import RefreshToken
from app.utils.user_code import generate_user_code
from app.audit.audit_services import create_audit_log
from sqlalchemy.exc import IntegrityError


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):

    # ✅ Check if email already exists
    existing_user = db.query(User).filter(
        User.email == payload.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

   
    role = db.query(Role).filter(
        Role.name.ilike(payload.role)
    ).first()

    if not role:
        role = Role(name=payload.role)
        db.add(role)
        db.commit()
        db.refresh(role)

    try:
      
        user = User(
            user_code=generate_user_code(),
            first_name =payload.first_name,
            last_name=payload.last_name,
            username=payload.email,
            # full_name=payload.full_name,
            email=payload.email,
            password_hash=get_password_hash(payload.password),
            role_id=role.id,
            is_active=payload.is_active
            
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    # ✅ Create audit log AFTER successful commit
    create_audit_log(
        db=db,
        module="AUTH",
        username=user.email,
        action="REGISTER",
        status="SUCCESS",
        description=f"User {user.email} registered successfully",
        request=request
    )

    return {
        "message": "User registered successfully",
        "user_code": user.user_code,
        "email": user.email,
        "role": role.name,
        "first_name":user.first_name,
        "last_name":user.last_name,
        "status": user.is_active
    }

@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, payload.email.lower(), payload.password)

    if not user:
        create_audit_log(
            db=db,
            module="AUTH",
            username=payload.email,
            action="LOGIN",
            status="FAILED",
            description=f"Failed login attempt for email {payload.email}",
            request=request
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        create_audit_log(
            db=db,
            module="AUTH",
            username=user.email,
            action="LOGIN",
            status="FAILED",
            description=f"Login attempt for disabled user {user.email}",
            request=request
        )
        raise HTTPException(status_code=403, detail="User account is disabled")

    access_token = create_access_token(user)
    refresh_token = create_refresh_token()

    db_token = RefreshToken(
        token=refresh_token,
        user_id=user.id
    )
    db.add(db_token)
    db.commit()

    create_audit_log(
        db=db,
        module="AUTH",
        username=user.email,
        action="LOGIN",
        status="SUCCESS",
        description=f"User {user.email} logged in successfully",
        request=request
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "user_code": user.user_code,
            # "full_name": user.full_name,
            "email": user.email,
            "role": user.role.name,
            "is_active": user.is_active
        }
    }