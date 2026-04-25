
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.core.database import Base
from sqlalchemy.sql import func
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, nullable=True)
    username = Column(String, nullable=True)

    module = Column(String, nullable=False)
    action = Column(String, nullable=False)

    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)

    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    status = Column(String, nullable=False)

    remote_ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # ✅ ADD THIS LINE
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    log_type = Column(String, nullable=False)
    