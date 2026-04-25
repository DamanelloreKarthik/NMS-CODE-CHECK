from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import INET
from database import Base   



# =====================================================
# DEVICES
# =====================================================

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    ip_address = Column(INET, unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False)  # switch, router, firewall
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    credentials = relationship(
        "DeviceCredential",
        back_populates="device",
        cascade="all, delete-orphan"
    )

    path_runs = relationship(
        "PathRun",
        back_populates="device",
        cascade="all, delete-orphan"
    )


# =====================================================
# DEVICE CREDENTIALS (ENCRYPTED - SOLARWINDS STYLE)
# =====================================================

class DeviceCredential(Base):
    __tablename__ = "device_credentials"

    id = Column(Integer, primary_key=True, index=True)

    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False
    )

    username = Column(String(100), nullable=False)

    # 🔐 ENCRYPTED PASSWORD STORED HERE
    encrypted_password = Column(String, nullable=False)

    is_primary = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    device = relationship("Device", back_populates="credentials")


# =====================================================
# PATH RUN (Traceroute Execution Record)
# =====================================================

class PathRun(Base):
    __tablename__ = "path_runs"

    id = Column(Integer, primary_key=True, index=True)

    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False
    )

    destination_ip = Column(INET, nullable=False)
    port = Column(Integer, nullable=True)

    status = Column(String(50), default="completed")  # completed / failed
    executed_at = Column(DateTime, server_default=func.now())

    # Relationships
    device = relationship("Device", back_populates="path_runs")

    hops = relationship(
        "PathHop",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="PathHop.hop_number"
    )


# =====================================================
# PATH HOPS (Each hop in traceroute)
# =====================================================

class PathHop(Base):
    __tablename__ = "path_hops"

    id = Column(Integer, primary_key=True, index=True)

    run_id = Column(
        Integer,
        ForeignKey("path_runs.id", ondelete="CASCADE"),
        nullable=False
    )

    hop_number = Column(Integer, nullable=False)

    ip_address = Column(INET, nullable=True)

    latency_min = Column(Float, nullable=True)
    latency_avg = Column(Float, nullable=True)
    latency_max = Column(Float, nullable=True)

    packet_loss_percent = Column(Float, default=0.0)

    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    run = relationship("PathRun", back_populates="hops")    


