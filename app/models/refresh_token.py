import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String, unique=True, nullable=False)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)


    expires_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(days=7)
    )

    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="refresh_tokens")
