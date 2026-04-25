
from sqlalchemy import Column, String, Integer, BigInteger, Text, DateTime, JSON, CheckConstraint
from sqlalchemy.sql import func
from database import Base

class Syslog(Base):
    __tablename__ = "syslogs"

    __table_args__ = (
        CheckConstraint("length(raw) <= 4096", name="ck_syslog_raw_length"),
    )

    id = Column(BigInteger, primary_key=True, index=True)

    timestamp = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())

    host = Column(String(255), nullable=False, index=True)
    hostname = Column(String(255))

    app_name = Column(String(128))
    process = Column(String(128))

    message = Column(Text, nullable=False)
    raw = Column(Text, nullable=False)

    severity = Column(String(16), index=True)
    facility = Column(String(32))

    os_type = Column(String(32), index=True)
    device_type = Column(String(32))

    protocol = Column(String(8))
    source_port = Column(Integer)

    tags = Column(JSON)