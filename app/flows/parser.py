from app.db_utils import safe_commit
from datetime import datetime

# NetFlow/IPFIX normalization based on standard flow record structures
# This implementation follows industry-standard network flow formats
# with minimal project-specific adaptation

def normalize_flow(
    *,
    exporter_ip: str,
    src_ip: str,
    dst_ip: str,
    src_port: int | None,
    dst_port: int | None,
    protocol: int,
    packets: int,
    bytes_count: int,
    flow_start: datetime,
    flow_end: datetime,
    ingress_if: int | None = None,
    egress_if: int | None = None,
    tcp_flags: int | None = None,
    application: str | None = None,
    direction: str = "ingress",
    flow_type: str = "netflow",
):


    return {
        "exporter_ip": exporter_ip,
        "exporter_name": None,
        "ingress_if": ingress_if,
        "egress_if": egress_if,

        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "protocol": protocol,

        "src_port": src_port,
        "dst_port": dst_port,
        "tcp_flags": tcp_flags,

        "packets": packets,
        "bytes": bytes_count,

        "flow_start": flow_start,
        "flow_end": flow_end,
        "received_at": datetime.utcnow(),

        "application": application,
        "direction": direction,
        "export_protocol": flow_type,
    }






