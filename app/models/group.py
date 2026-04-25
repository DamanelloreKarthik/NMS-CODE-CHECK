import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)