import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class PersonalAccessToken(Base):
    __tablename__ = "personal_access_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(100), nullable=False)
    description = Column(Text)

    token = Column(String, unique=True, nullable=False)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    created_by = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    expires_at = Column(DateTime(timezone=True))

    is_active = Column(Boolean, default=True)

    # ✅ Relationship (optional but useful)
    user = relationship("User")