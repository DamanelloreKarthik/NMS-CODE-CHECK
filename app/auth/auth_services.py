
import uuid
from typing import Optional
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models import User, RefreshToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def authenticate_user(
    db: Session,
    username: str,
    password: str
) -> Optional[User]:
    user = get_user_by_username(db, username)

    if not user:
        return None

    if not user.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user



def create_refresh_token(db: Session, user_id: int) -> str:
    token = str(uuid.uuid4())

    refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)

    return token

