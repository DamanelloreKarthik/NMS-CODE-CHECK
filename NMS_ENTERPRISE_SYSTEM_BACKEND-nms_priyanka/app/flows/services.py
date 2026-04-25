
from datetime import datetime, timedelta
from sqlalchemy import or_, func
from app.flows.models import NetFlowRecord 
from datetime import timezone



# -------------------------
# CONFIG
# -------------------------
FLOW_TIMEOUT = 30  # seconds


# -------------------------
# PROTOCOL NAME
# -------------------------
def get_protocol_name(proto):
    return {
        6: "TCP",
        17: "UDP",
        1: "ICMP"
    }.get(proto, "OTHER")


# -------------------------
# INTERNAL IP CHECK
# -------------------------
import ipaddress

def is_internal_ip(ip):
    try:
        return ipaddress.ip_address(str(ip)).is_private
    except ValueError:
        return False


# -------------------------
# DIRECTION LOGIC (FIXED)
# -------------------------
def get_flow_direction(src_ip, dst_ip):
    src_internal = is_internal_ip(src_ip)
    dst_internal = is_internal_ip(dst_ip)

    if src_internal and dst_internal:
        return "INTERNAL"
    elif src_internal:
        return "OUTBOUND"
    else:
        return "INBOUND"

# Explorer and dashboard
# -------------------------
# PROTOCOL CLASSIFICATION
# -------------------------
def classify_protocol(protocol, src_port, dst_port):

    # smarter port detection (server-side)
    if dst_port and dst_port < 1024:
        port = dst_port
    elif src_port and src_port < 1024:
        port = src_port
    else:
        port = dst_port or src_port

    # ICMP fix
    if protocol == 1:
        return "ICMP"

     # ✅ INTERNAL CUSTOM PORTS (ADD HERE)
    # -------------------------
    internal_ports = {
        2233: "Camera-Control",
        5500: "Device-Management",
        9080: "Internal-Web-UI",
        12321: "Cluster-Heartbeat"
    }

    if port in internal_ports:
        return internal_ports[port]

    common_ports = {
        80: "HTTP",
        443: "HTTPS",
        22: "SSH",
        21: "FTP",
        53: "DNS",
        123: "NTP",
        25: "SMTP",
        110: "POP3",
        143: "IMAP",
        554: "RTSP",
        3389: "RDP",
        3306: "MySQL",
        1433: "MSSQL",
        6379: "Redis",
        27017: "MongoDB",
        161: "SNMP",
        162: "SNMP-TRAP",
        8080: "HTTP-ALT",
        8443: "HTTPS-ALT",

        # ✅ NEW (reduces Unknown significantly)
        9092: "Kafka",
        5432: "PostgreSQL",
        1521: "Oracle",
        8081: "HTTP-ALT",
        7001: "WebLogic",
        5601: "Kibana",
        9200: "Elasticsearch",
        5672: "RabbitMQ",
        389: "LDAP",
        636: "LDAPS",
        445: "SMB",
        135: "RPC",
        139: "NetBIOS",
        1900: "UPnP",
        5060: "SIP",
        5061: "SIP-TLS",
        1812: "RADIUS",
        1813: "RADIUS-Accounting",
        3000: "Grafana",
        6443: "Kubernetes",
        2379: "etcd",
        10250: "Kubelet",
        
    }

    if port in common_ports:
        return common_ports[port]

    return "OTHER"

# explorer
# -------------------------
# APPLICATION ENRICHMENT
# -------------------------
def enrich_application(app, dst_ip):

    if app == "HTTPS":
        if dst_ip.startswith("172.217") or dst_ip.startswith("142.250"):
            return "Google Services"
        if dst_ip.startswith("52.114"):
            return "Microsoft Teams"
        if dst_ip.startswith("13.107"):
            return "Microsoft Services"

    return app

def get_timeline(query, start_time, end_time):
    rows = query.with_entities(
        func.date_trunc('minute', NetFlowRecord.flow_start).label("time_bucket"),
        func.count().label("events")
    ).group_by("time_bucket").order_by("time_bucket").all()

    # Convert DB result to dict
    data_map = {
        r.time_bucket.strftime("%H:%M"): r.events
        for r in rows
    }

    # ✅ Fill missing minutes
    timeline = []
    current = start_time.replace(second=0, microsecond=0)

    while current <= end_time:
        key = current.strftime("%H:%M")

        timeline.append({
            "time": key,
            "events": data_map.get(key, 0)  # ✅ fill missing with 0
        })

        current += timedelta(minutes=1)

    return timeline
# -------------------------
# FLOW STATUS
# -------------------------
def get_flow_status(flow_start, flow_end):
    now = datetime.now(timezone.utc)

    last_seen = flow_end if flow_end and flow_end > flow_start else flow_start

    if (now - last_seen).total_seconds() > FLOW_TIMEOUT:
        return "CLOSED"

    return "ACTIVE"


# -------------------------
# DURATION (IMPROVED)
# -------------------------
def get_duration(flow_start, flow_end):
    if not flow_start:
        return "0s"

    if flow_end and flow_end > flow_start:
        duration = (flow_end - flow_start).total_seconds()
    else:
        duration = 0

    # ✅ Fix: show <1s instead of 0s
    if duration < 1:
        return "<1s"

    return f"{round(duration, 1)}s"


# -------------------------
# FORMATTERS
# -------------------------
def format_bytes(bytes_val):
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024**2:
        return f"{round(bytes_val / 1024, 1)} KB"
    elif bytes_val < 1024**3:
        return f"{round(bytes_val / (1024**2), 1)} MB"
    else:
        return f"{round(bytes_val / (1024**3), 1)} GB"


def format_bytes_struct(bytes_val):
    if bytes_val < 1024:
        return {"value": bytes_val, "unit": "B", "raw": bytes_val}
    elif bytes_val < 1024**2:
        return {"value": round(bytes_val / 1024, 1), "unit": "KB", "raw": bytes_val}
    elif bytes_val < 1024**3:
        return {"value": round(bytes_val / (1024**2), 1), "unit": "MB", "raw": bytes_val}
    else:
        return {"value": round(bytes_val / (1024**3), 1), "unit": "GB", "raw": bytes_val}

# Dashboard & explorer
# -------------------------
# BASE FILTER QUERY
# -------------------------
def base_query(db, start_time, end_time, event_source=None, interface=None):
    query = db.query(NetFlowRecord).filter(
        NetFlowRecord.flow_end >= start_time,
        NetFlowRecord.flow_start <= end_time
    )

    if event_source:
        query = query.filter(NetFlowRecord.exporter_ip == event_source)

    if interface:
        query = query.filter(NetFlowRecord.ingress_if == interface)

    return query

# explorer#
# -------------------------
# EXPLORER FILTERS
# -------------------------
def apply_explorer_filters(query, source_ip=None, destination_ip=None, port=None, protocol=None):

    if source_ip:
        query = query.filter(NetFlowRecord.src_ip == source_ip)

    if destination_ip:
        query = query.filter(NetFlowRecord.dst_ip == destination_ip)

    if port:
        query = query.filter(
            or_(
                NetFlowRecord.src_port == port,
                NetFlowRecord.dst_port == port
            )
        )

    if protocol:
        query = query.filter(NetFlowRecord.protocol == protocol)

    return query   

def calculate_throughput(bytes_val, seconds):
    if seconds <= 0 or not bytes_val:
        return 0.0

    bytes_val = float(bytes_val)

    # ✅ Correct Mbps calculation (NO scaling)
    return round((bytes_val * 8) / (seconds * 1_000_000), 4)

# -------------------------
# FLOW OVERVIEW (KPIs)
# -------------------------
def get_flow_overview(query, start_time, end_time):

    total_flows = query.count()
    total_bytes = query.with_entities(func.sum(NetFlowRecord.bytes)).scalar() or 0

    seconds = max((end_time - start_time).total_seconds(), 1)

    avg_throughput = calculate_throughput(total_bytes, seconds)

    active_sessions = query.filter(NetFlowRecord.flow_end.is_(None)).count()

    unique_assets = query.with_entities(NetFlowRecord.src_ip).distinct().count()

    return {
        "total_flows": total_flows,
        "avg_throughput_mbps": avg_throughput,
        "active_sessions": active_sessions,
        "unique_assets": unique_assets
    }



# -------------------------
# TOP TALKERS
# -------------------------
def get_top_talkers(query, limit=5):

    rows = query.with_entities(
        NetFlowRecord.src_ip,
        func.sum(NetFlowRecord.bytes).label("bytes")
    ).group_by(NetFlowRecord.src_ip)\
     .order_by(func.sum(NetFlowRecord.bytes).desc())\
     .limit(limit)\
     .all()

    total = sum(r.bytes for r in rows) or 1

    return [
        {
            "ip": str(r.src_ip),
            "bytes": r.bytes,
            "percentage": round((r.bytes / total) * 100, 2)
        }
        for r in rows
    ]


# -------------------------
# PATTERN RECOGNITION
# -------------------------
def get_pattern_recognition(query):

    top_port = query.with_entities(
        NetFlowRecord.dst_port,
        func.count().label("count")
    ).group_by(NetFlowRecord.dst_port)\
     .order_by(func.count().desc())\
     .first()

    top_protocol = query.with_entities(
        NetFlowRecord.protocol,
        func.count().label("count")
    ).group_by(NetFlowRecord.protocol)\
     .order_by(func.count().desc())\
     .first()

    # ✅ FIX: add order_by + limit(10)
    repeated_flows = query.with_entities(
        NetFlowRecord.src_ip,
        NetFlowRecord.dst_ip,
        func.count().label("count")
    ).group_by(NetFlowRecord.src_ip, NetFlowRecord.dst_ip)\
     .having(func.count() > 50)\
     .order_by(func.count().desc())\
     .limit(10)\
     .all()

    return {
        "top_port": top_port.dst_port if top_port else None,
        "top_port_usage": top_port.count if top_port else 0,
        "top_protocol": get_protocol_name(top_protocol.protocol) if top_protocol else None,
        "top_protocol_usage": top_protocol.count if top_protocol else 0,
        "repeated_flows": [
            {
                "source": str(r.src_ip),
                "destination": str(r.dst_ip),
                "count": r.count
            }
            for r in repeated_flows
        ]
    }
# -------------------------
# INTELLIGENT INSIGHTS
# -------------------------
def get_intelligent_insights(query):

    insights = []

    # -------------------------
    # UDP SPIKE DETECTION
    # -------------------------
    total_flows = query.count() or 1

    udp_flows = query.filter(NetFlowRecord.protocol == 17).count()
    udp_ratio = udp_flows / total_flows

    if udp_ratio > 0.5:
        insights.append({
            "type": "HIGH_UDP_ACTIVITY",
            "message": "Unusual spike in UDP traffic detected"
        })

    # -------------------------
    # SAFE PROTOCOL CHECK (HTTPS)
    # -------------------------
    https_bytes = query.filter(
        or_(
            NetFlowRecord.dst_port == 443,
            NetFlowRecord.src_port == 443
        )
    ).with_entities(func.sum(NetFlowRecord.bytes)).scalar() or 0

    total_bytes = query.with_entities(
        func.sum(NetFlowRecord.bytes)
    ).scalar() or 1

    https_ratio = https_bytes / total_bytes

    if https_ratio > 0.5:
        insights.append({
            "type": "SAFE_PROTOCOLS",
            "message": "Majority traffic is encrypted"
        })

    return insights


def detect_anomalies(trends):
    if not trends:
        return []

    values = [t["throughput_mbps"] for t in trends]
    avg = sum(values) / len(values)

    anomalies = []

    for t in trends:
        if t["throughput_mbps"] > avg * 1.8:  # spike
            anomalies.append({
                "type": "TRAFFIC_SPIKE",
                "time": t["time"],
                "value": t["throughput_mbps"]
            })

    return anomalies
         


def get_latency_distribution(query):
    rows = query.with_entities(NetFlowRecord.flow_start, NetFlowRecord.flow_end).all()

    latencies = []

    for r in rows:
        if r.flow_start and r.flow_end and r.flow_end > r.flow_start:
            latencies.append((r.flow_end - r.flow_start).total_seconds() * 1000)  # ms

    if not latencies:
        return {"p50": 0, "p95": 0, "p99": 0}

    latencies.sort()
    n = len(latencies)

    return {
        "p50": round(latencies[int(n * 0.5)], 2),
        "p95": round(latencies[int(n * 0.95)], 2),
        "p99": round(latencies[int(n * 0.99)], 2)
    }
       
def get_performance_trends(query, start_time, end_time):
    rows = query.with_entities(
        func.date_trunc('minute', NetFlowRecord.flow_start).label("time_bucket"),
        func.sum(NetFlowRecord.bytes).label("bytes")
    ).group_by("time_bucket").order_by("time_bucket").all()

    data_map = {
        r.time_bucket.strftime("%H:%M"): r.bytes or 0
        for r in rows
    }

    result = []
    current = start_time.replace(second=0, microsecond=0)

    while current <= end_time:
        key = current.strftime("%H:%M")
        bytes_val = data_map.get(key, 0)

        mbps = calculate_throughput(bytes_val, 60)

        result.append({
            "time": key,
            "throughput_mbps": mbps
        })

        current += timedelta(minutes=1)

    return result      

