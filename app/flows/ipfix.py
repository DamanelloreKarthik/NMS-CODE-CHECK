from app.db_utils import safe_commit
import socket
import struct
import logging
from datetime import datetime
from app.flows.parser import normalize_flow
from database import SessionLocal
from app.flows.models import NetFlowRecord
from app.core.redis_client import save_ipfix_template, get_ipfix_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IPFIX")

UDP_IP = "0.0.0.0"
UDP_PORT = 4739
BUFFER_SIZE = 65535



# MAIN LISTENER

def start_ipfix_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    logger.info(f"IPFIX listener started on {UDP_IP}:{UDP_PORT}")

    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        exporter_ip = addr[0]

        if len(data) < 16:
            continue

        version = struct.unpack("!H", data[:2])[0]

        if version != 10:
            continue

        parse_ipfix_packet(data, exporter_ip)



# IPFIX PACKET PARSER

def parse_ipfix_packet(data, exporter_ip):
    try:
        version, length, export_time, sequence, domain_id = struct.unpack(
            "!HHIII", data[:16]
        )

        payload = data[16:length]
        offset = 0

        while offset + 4 <= len(payload):
            set_id, set_length = struct.unpack(
                "!HH", payload[offset:offset+4]
            )

            if set_length < 4:
                break

            set_data = payload[offset+4:offset+set_length]

            if set_id == 2:
                parse_template_set(set_data, exporter_ip, domain_id)

            elif set_id >= 256:
                parse_data_set(set_id, set_data, exporter_ip, domain_id)

            offset += set_length

    except Exception as e:
        logger.error(f"IPFIX packet parse error: {e}")



# TEMPLATE SET PARSER

def parse_template_set(data, exporter_ip, domain_id):
    offset = 0

    while offset + 4 <= len(data):
        template_id, field_count = struct.unpack(
            "!HH", data[offset:offset+4]
        )
        offset += 4

        fields = []

        for _ in range(field_count):
            if offset + 4 > len(data):
                break

            field_type, field_length = struct.unpack(
                "!HH", data[offset:offset+4]
            )
            offset += 4
            fields.append((field_type, field_length))

        # REDIS STORE
        save_ipfix_template(exporter_ip, domain_id, template_id, fields)

        logger.info(
            f"Stored IPFIX template {template_id} "
            f"from {exporter_ip}"
        )



# DATA SET PARSER

def parse_data_set(template_id, data, exporter_ip, domain_id):
    # REDIS FETCH
    fields = get_ipfix_template(exporter_ip, domain_id, template_id)

    if not fields:
        logger.warning(
            f"No IPFIX template {template_id} from {exporter_ip}"
        )
        return

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

        save_ipfix_record(record_data, exporter_ip)

        offset += record_length


def save_ipfix_record(record_data, exporter_ip):
    try:
        src_ip = socket.inet_ntoa(record_data[8]) if 8 in record_data else None
        dst_ip = socket.inet_ntoa(record_data[12]) if 12 in record_data else None

        src_port = int.from_bytes(record_data.get(7, b'\x00'), "big")
        dst_port = int.from_bytes(record_data.get(11, b'\x00'), "big")
        protocol = int.from_bytes(record_data.get(4, b'\x00'), "big")

        packets = int.from_bytes(record_data.get(2, b'\x00'), "big")
        bytes_count = int.from_bytes(record_data.get(1, b'\x00'), "big")

        now = datetime.utcnow()

        normalized = normalize_flow(
            exporter_ip=exporter_ip,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
            packets=packets,
            bytes_count=bytes_count,
            flow_start=now,
            flow_end=now,
            direction="ingress",
            flow_type="ipfix"
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
            safe_commit(db)
        except Exception as e:
            db.rollback()
            logger.error(f"DB Insert Error: {e}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"IPFIX record parse error: {e}")