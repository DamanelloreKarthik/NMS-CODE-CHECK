# import uuid
# from sqlalchemy import Column, String, Text, ForeignKey
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import relationship

# from app.core.database import Base


# class UserProfile(Base):
#     __tablename__ = "user_profiles"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

#     name = Column(String(100), unique=True, nullable=False)
#     description = Column(Text)

#     scope_by = Column(String(20))  # "User" or "Group"

#     # ✅ NEW FIELDS
#     user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
#     role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
#     group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=True)

#     # ✅ Relationships (IMPORTANT for showing names)
#     user = relationship("User")
#     role = relationship("Role")
#     group = relationship("Group")

from sqlalchemy import Column, String, ForeignKey
from app.core.database import Base
import uuid

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    scope_by = Column(String, nullable=False)

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role_id = Column(String, ForeignKey("roles.id"), nullable=False)
    group_id = Column(String, ForeignKey("groups.id"), nullable=True)  # optional



    class Group(Base):
     __tablename__ = "groups"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)