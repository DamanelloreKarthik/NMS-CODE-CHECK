
import socket
import struct
import logging
from datetime import datetime, timezone, timedelta
from database import SessionLocal
from app.flows.models import NetFlowRecord 
from app.flows.parser import normalize_flow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NETFLOW")

UDP_IP = "0.0.0.0"
UDP_PORT = 9996
BUFFER_SIZE = 65535

# For NetFlow v9 templates
templates_v9 = {}


# --------------------------------------------------
# MAIN LISTENER
# --------------------------------------------------
def start_netflow_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    logger.info(f"🚀 NetFlow listener started on {UDP_IP}:{UDP_PORT}")

    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        exporter_ip = addr[0]

        if len(data) < 2:
            continue

        version = struct.unpack("!H", data[:2])[0]

        if version == 5:
            parse_netflow_v5(data, exporter_ip)

        elif version == 9:
            parse_netflow_v9(data, exporter_ip)

        else:
            logger.warning(f"Unsupported NetFlow version {version}")


# --------------------------------------------------
# NETFLOW V5
# --------------------------------------------------
def parse_netflow_v5(data, exporter_ip):
    header = struct.unpack("!HHIIIIBBH", data[:24])
    count = header[1]

    # ✅ Extract timing info (PR FIX)
    sys_uptime = header[2]
    unix_secs = header[3]

    offset = 24
    for _ in range(count):
        record = struct.unpack("!IIIHHIIIIHHBBBBHHBBH", data[offset:offset+48])

        src_ip = socket.inet_ntoa(struct.pack("!I", record[0]))
        dst_ip = socket.inet_ntoa(struct.pack("!I", record[1]))

        packets = record[4]
        bytes_count = record[5]
        src_port = record[9]
        dst_port = record[10]
        protocol = record[13]

        # ✅ Extract flow timing (PR FIX)
        first = record[6]
        last = record[7]

        flow_end = datetime.fromtimestamp(unix_secs, timezone.utc)
        flow_start = flow_end - timedelta(milliseconds=(sys_uptime - first))

        save_flow(
            exporter_ip,
            src_ip,
            dst_ip,
            src_port,
            dst_port,
            protocol,
            packets,
            bytes_count,
            "netflow_v5",
            flow_start=flow_start,
            flow_end=flow_end
        )

        offset += 48


# --------------------------------------------------
# NETFLOW V9 (Template Based)
# --------------------------------------------------
def parse_netflow_v9(data, exporter_ip):
    header = struct.unpack("!HHIIII", data[:20])
    count = header[1]

    offset = 20

    while offset < len(data):
        flowset_id, length = struct.unpack("!HH", data[offset:offset+4])
        flowset_data = data[offset+4:offset+length]

        if flowset_id == 0:
            parse_v9_template(flowset_data, exporter_ip)

        elif flowset_id >= 256:
            parse_v9_data(flowset_id, flowset_data, exporter_ip)

        offset += length


def parse_v9_template(data, exporter_ip):
    offset = 0

    while offset + 4 <= len(data):
        template_id, field_count = struct.unpack("!HH", data[offset:offset+4])
        offset += 4

        fields = []
        for _ in range(field_count):
            field_type, field_length = struct.unpack("!HH", data[offset:offset+4])
            offset += 4
            fields.append((field_type, field_length))

        templates_v9[(exporter_ip, template_id)] = fields

        logger.info(f"Stored NetFlow v9 template {template_id}")


def parse_v9_data(template_id, data, exporter_ip):
    key = (exporter_ip, template_id)

    if key not in templates_v9:
        return

    fields = templates_v9[key]
    record_length = sum(length for _, length in fields)

    offset = 0

    while offset + record_length <= len(data):
        record_raw = data[offset:offset+record_length]
        field_offset = 0
        record_data = {}

        for field_type, field_length in fields:
            value = record_raw[field_offset:field_offset+field_length]
            field_offset += field_length
            record_data[field_type] = value

        save_v9_record(record_data, exporter_ip)

        offset += record_length


# --------------------------------------------------
# SAVE HELPERS
# --------------------------------------------------
def save_v9_record(record_data, exporter_ip):
    try:
        src_ip = socket.inet_ntoa(record_data[8]) if 8 in record_data else None
        dst_ip = socket.inet_ntoa(record_data[12]) if 12 in record_data else None

        packets = int.from_bytes(record_data.get(2, b'\x00'), "big")
        bytes_count = int.from_bytes(record_data.get(1, b'\x00'), "big")

        src_port = int.from_bytes(record_data.get(7, b'\x00'), "big")
        dst_port = int.from_bytes(record_data.get(11, b'\x00'), "big")

        protocol = int.from_bytes(record_data.get(4, b'\x00'), "big")

        # ✅ v9 fallback (PR SAFE)
        save_flow(
            exporter_ip,
            src_ip,
            dst_ip,
            src_port,
            dst_port,
            protocol,
            packets,
            bytes_count,
            "netflow_v9",
            flow_start=None,
            flow_end=None
        )

    except Exception as e:
        logger.error(f"NetFlow v9 parse error: {e}")





def save_flow(exporter_ip, src_ip, dst_ip, src_port, dst_port,
              protocol, packets, bytes_count, export_protocol,
              flow_start=None, flow_end=None):

    now = datetime.now(timezone.utc)

    normalized = normalize_flow(
        exporter_ip=exporter_ip,
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        protocol=protocol,
        packets=packets,
        bytes_count=bytes_count,
        flow_start=flow_start or now,
        flow_end=flow_end or now,
        direction="ingress",
        flow_type=export_protocol
    )

    allowed_fields = {
        "exporter_ip", "exporter_name",
        "ingress_if", "egress_if",
        "src_ip", "dst_ip",
        "protocol",
        "src_port", "dst_port", "tcp_flags",
        "packets", "bytes",
        "flow_start", "flow_end", "received_at",
        "direction"
    }

    clean_record = {k: v for k, v in normalized.items() if k in allowed_fields}

    db = SessionLocal()
    try:
        db.add(NetFlowRecord(**clean_record))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"DB Insert Error: {e}")
    finally:
        db.close()

    logger.info(f"✅ Flow saved {src_ip}:{src_port} → {dst_ip}:{dst_port}")