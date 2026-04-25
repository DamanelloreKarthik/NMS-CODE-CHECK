import socket
import logging
from datetime import datetime, timezone

import dpkt

from database import SessionLocal
from app.flows.models import NetFlowRecord
from app.flows.parser import normalize_flow

logger = logging.getLogger(__name__)

SFLOW_IP = "0.0.0.0"
SFLOW_PORT = 6343


def parse_raw_packet(packet_data):
    try:
        eth = dpkt.ethernet.Ethernet(packet_data)

        if not isinstance(eth.data, dpkt.ip.IP):
            return None

        ip = eth.data

        src_ip = socket.inet_ntoa(ip.src)
        dst_ip = socket.inet_ntoa(ip.dst)
        protocol = ip.p

        src_port = None
        dst_port = None
        tcp_flags = None

        if isinstance(ip.data, dpkt.tcp.TCP):
            src_port = ip.data.sport
            dst_port = ip.data.dport
            tcp_flags = ip.data.flags

        elif isinstance(ip.data, dpkt.udp.UDP):
            src_port = ip.data.sport
            dst_port = ip.data.dport

        return {
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "protocol": protocol,
            "src_port": src_port,
            "dst_port": dst_port,
            "tcp_flags": tcp_flags,
        }

    except Exception as exc:
        logger.warning("sFlow packet parse failed: %s", exc)
        return None


def start_sflow_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SFLOW_IP, SFLOW_PORT))
    print("🚀 Production sFlow Listener started on port 6343")

    while True:
        data, addr = sock.recvfrom(65535)
        exporter_ip = addr[0]
        now = datetime.now(timezone.utc)

        try:
            raw_packet = None

            for i in range(0, len(data) - 2):
                if data[i:i+2] == b'\x08\x00':
                    raw_packet = data[i-12:]
                    break

            if not raw_packet:
                continue

            parsed = parse_raw_packet(raw_packet)
            if not parsed:
                continue

            normalized = normalize_flow(
                exporter_ip=exporter_ip,
                src_ip=parsed["src_ip"],
                dst_ip=parsed["dst_ip"],
                src_port=parsed["src_port"],
                dst_port=parsed["dst_port"],
                protocol=parsed["protocol"],
                packets=1,
                bytes_count=len(raw_packet),
                flow_start=now,
                flow_end=now,
                tcp_flags=parsed["tcp_flags"],
                direction="ingress",
                flow_type="sflow"
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
                logger.error("DB insert error: %s", e)
            finally:
                db.close()

        except Exception as e:
            logger.error("sFlow parse error: %s", e)