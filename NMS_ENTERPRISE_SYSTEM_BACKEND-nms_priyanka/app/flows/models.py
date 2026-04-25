
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    SmallInteger,
    String,
    TIMESTAMP,
    Index
)
from sqlalchemy.dialects.postgresql import INET
from database import Base


class NetFlowRecord(Base):
    __tablename__ = "flow_records"

    id = Column(BigInteger, primary_key=True)

    # -------- Device / Exporter --------
    exporter_ip = Column(INET, index=True)
    exporter_name = Column(String(64), nullable=True)
    ingress_if = Column(Integer, nullable=True)
    egress_if = Column(Integer, nullable=True)

    # -------- Layer 3 --------
    src_ip = Column(INET, index=True)
    dst_ip = Column(INET, index=True)
    protocol = Column(SmallInteger)

    # -------- Layer 4 --------
    src_port = Column(Integer, nullable=True)
    dst_port = Column(Integer, nullable=True)
    tcp_flags = Column(Integer, nullable=True)
    tos = Column(Integer, nullable=True)

    # -------- Counters --------
    packets = Column(BigInteger)
    bytes = Column(BigInteger)

    # -------- Time --------
    flow_start = Column(TIMESTAMP, index=True)
    flow_end = Column(TIMESTAMP, index=True)
    received_at = Column(TIMESTAMP)

    # -------- Classification --------
    direction = Column(String(10))
    export_protocol = Column(String(16))   # THIS matches your DB check constraint


# Index already exists in DB, keep this if needed
Index("idx_flow_time_range", NetFlowRecord.flow_start, NetFlowRecord.flow_end)





