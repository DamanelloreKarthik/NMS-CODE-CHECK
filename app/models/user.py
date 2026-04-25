
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey # <--- JSON MUST BE HERE


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(100), unique=True, nullable=False)
    description = Column(String)
    permissions_metadata = Column(JSON, nullable=True, default={})
  
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    users = relationship(
        "User",
        back_populates="role",
        lazy="selectin",
    )

    role_permissions = relationship(
        "RolePermission",
        back_populates="role",
        lazy="selectin",
        cascade="all, delete-orphan"
    )



class User(Base):
    __tablename__ = "users"

    user_code = Column(String(10), unique=True, nullable=False)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

  
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)

    mobile_number = Column(String(20))

    password_hash = Column(String, nullable=False)

    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL")
    )

    role = relationship(
        "Role",
        back_populates="users",
        lazy="selectin",
    )


    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    module = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    role_permissions = relationship(
        "RolePermission",
        back_populates="permission",
        lazy="selectin"
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True
    )

    permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    role = relationship(
        "Role",
        back_populates="role_permissions"
    )

    permission = relationship(
        "Permission",
        back_populates="role_permissions"
    )
