
import paramiko
import re
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import ipaddress   # ✅ ADDED (for IP validation)
from datetime import timezone
from app.path_analysis.models import Device, DeviceCredential, PathRun, PathHop
from app.flows.models import NetFlowRecord
from app.path_analysis.utils.security import decrypt_password   
import logging


logger = logging.getLogger(__name__)


# ==========================================================
# SAFE HELPERS (ADDED ONLY FOR SECURITY FIX)
# ==========================================================
def safe_ip(ip: str) -> str:
    return str(ipaddress.ip_address(ip))


def safe_port(port: int) -> int:
    if not (1 <= port <= 65535):
        raise ValueError("Invalid port")
    return port


# ==========================================================
# DESTINATION OPTIONS (FILTER API)
# ==========================================================
def get_destination_options(db, source_ip: str):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=60)

    top_talkers_raw = get_top_talkers(db, source_ip=source_ip,minutes=60, limit=3)

    return {
        "manual_allowed": True,
        "top_talkers": [{"ip": t["ip"]} for t in top_talkers_raw],
        "predefined": [
            {"ip": "8.8.8.8", "label": "Google DNS"},
            {"ip": "1.1.1.1", "label": "Cloudflare DNS"},
            {"ip": "20.205.243.166", "label": "Microsoft Azure"}
        ]
    }




# ==========================================================
# TOP TALKERS (UNIQUE DESTINATIONS ONLY)
# ==========================================================  

def get_top_talkers(db, source_ip=None, minutes=60, limit=3):
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)

        query = db.query(
            NetFlowRecord.dst_ip,
            func.sum(NetFlowRecord.bytes).label("total_bytes")
        ).filter(
            NetFlowRecord.flow_end >= start_time,
            NetFlowRecord.flow_start <= end_time
        )

        if source_ip:
            query = query.filter(NetFlowRecord.src_ip == source_ip)

        rows = (
            query
            .group_by(NetFlowRecord.dst_ip)
            .order_by(func.sum(NetFlowRecord.bytes).desc())
            .limit(limit)
            .all()
        )

        if not rows:
            logger.warning(
                "Top talkers fallback triggered | source_ip=%s",
                source_ip
            )

            rows = (
                db.query(
                    NetFlowRecord.dst_ip,
                    func.sum(NetFlowRecord.bytes).label("total_bytes")
                )
                .group_by(NetFlowRecord.dst_ip)
                .order_by(func.sum(NetFlowRecord.bytes).desc())
                .limit(limit)
                .all()
            )

        return [{"ip": str(r.dst_ip)} for r in rows]

    except Exception as e:
        logger.exception("Error in get_top_talkers")
        return []
# ==========================================================
# MAIN EXECUTION FUNCTION (TRACEROUTE)
# ==========================================================
def execute_traceroute(
    db: Session,
    device_id: int | None,
    device_name: str | None,
    device_ip: str | None,
    destination_ip: str,
    port: int | None = None
):

    query = db.query(Device)
    device = None

    if device_id:
        device = query.filter(Device.id == device_id).first()
    elif device_name:
        device = query.filter(Device.name.ilike(device_name)).first()
    elif device_ip:
        device = query.filter(Device.ip_address == device_ip).first()
    else:
        raise Exception("Provide device_id OR device_name OR device_ip")

    if not device:
        raise Exception("Device not found")

    credential = (
        db.query(DeviceCredential)
        .filter(
            DeviceCredential.device_id == device.id,
            DeviceCredential.is_primary == True
        )
        .first()
    )

    if not credential:
        raise Exception("Device credentials not found")

    password = decrypt_password(credential.encrypted_password)

    ssh = paramiko.SSHClient()

    # 🔴 FIX 2: SSH MITM PROTECTION (REPLACED)
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.RejectPolicy())

    try:
        ssh.connect(
            hostname=str(device.ip_address),
            username=credential.username,
            password=password,
            timeout=15
        )

        # 🔴 FIX 1: COMMAND INJECTION PROTECTION
        dest = safe_ip(destination_ip)
        p = safe_port(port) if port else None

        cmd = f"traceroute -p {p} {dest}" if p else f"traceroute {dest}"

        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=False)

        raw_output = stdout.read().decode(errors="ignore")
        error = stderr.read().decode(errors="ignore")

        if error.strip():
            raise Exception(f"Traceroute error: {error}")

    finally:
        ssh.close()

    path_run = PathRun(
        device_id=device.id,
        destination_ip=destination_ip,
        port=port,
        status="completed",
        executed_at= datetime.now(timezone.utc)
    )

    db.add(path_run)
    db.commit()
    db.refresh(path_run)

    parsed_hops = parse_traceroute_output(raw_output)

    for hop in parsed_hops:
        db.add(
            PathHop(
                run_id=path_run.id,
                hop_number=hop["hop_number"],
                ip_address=hop["ip_address"],
                latency_min=hop["latency_min"],
                latency_avg=hop["latency_avg"],
                latency_max=hop["latency_max"],
                packet_loss_percent=hop["packet_loss_percent"]
            )
        )

    db.commit()

    return {
        "run_id": path_run.id,
        "device_name": device.name,
        "device_ip": str(device.ip_address),
        "destination_ip": destination_ip,
        "executed_at": path_run.executed_at,
        "hops": parsed_hops
    }


# ==========================================================
# TRACEROUTE PARSER
# ==========================================================
def parse_traceroute_output(raw_output: str):
    hops = []
    lines = raw_output.splitlines()

    for line in lines:
        line = line.strip()

        if not line or line.lower().startswith("traceroute"):
            continue

        hop_match = re.match(r"^(\d+)\s+(.*)", line)
        if not hop_match:
            continue

        hop_number = int(hop_match.group(1))
        rest = hop_match.group(2)

        if re.fullmatch(r"\*+\s+\*+\s+\*+", rest):
            hops.append({
                "hop_number": hop_number,
                "ip_address": None,
                "latency_min": None,
                "latency_avg": None,
                "latency_max": None,
                "packet_loss_percent": 100
            })
            continue

        ip_match = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", rest)
        ip_address = ip_match.group(1) if ip_match else None

        latency_matches = re.findall(r"(\d+(?:\.\d+)?)\s*ms", rest)
        latencies = [float(x) for x in latency_matches]

        if latencies:
            latency_min = min(latencies)
            latency_max = max(latencies)
            latency_avg = sum(latencies) / len(latencies)
            packet_loss = round(((3 - len(latencies)) / 3) * 100, 2)
        else:
            latency_min = latency_avg = latency_max = None
            packet_loss = 100

        hops.append({
            "hop_number": hop_number,
            "ip_address": ip_address,
            "latency_min": latency_min,
            "latency_avg": latency_avg,
            "latency_max": latency_max,
            "packet_loss_percent": packet_loss
        })

    return hops


# ==========================================================
# UI FORMATTER
# ==========================================================
def format_path_response(raw_data: dict):
    hops = raw_data["hops"]

    valid_latencies = [
        h["latency_avg"]
        for h in hops if h["latency_avg"] is not None
    ]

    latency_min = min(valid_latencies) if valid_latencies else None
    latency_avg = sum(valid_latencies) / len(valid_latencies) if valid_latencies else None
    latency_max = max(valid_latencies) if valid_latencies else None

    packet_loss = max(h["packet_loss_percent"] for h in hops)
    transit_likelihood = 100 - packet_loss

    path = [
        {
            "hop": h["hop_number"],
            "ip": h["ip_address"],
            "latency": round(h["latency_avg"], 2) if h["latency_avg"] else None,
            "status": "down" if h["packet_loss_percent"] == 100 else "up"
        }
        for h in hops
    ]

    return {
        "summary": {
            "source": {
                "device_name": raw_data["device_name"],
                "ip": raw_data["device_ip"]
            },
            "destination": {
                "ip": raw_data["destination_ip"]
            },
            "latency": {
                "min": round(latency_min, 2) if latency_min else None,
                "avg": round(latency_avg, 2) if latency_avg else None,
                "max": round(latency_max, 2) if latency_max else None,
            },
            "packet_loss_percent": packet_loss,
            "transit_likelihood_percent": transit_likelihood
        },
        "path": path
    }


# ==========================================================
# PATH HISTORY (NEW)
# ==========================================================
def get_path_history(db, source_ip: str, destination_ip: str, minutes: int = 60):

    time_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    runs = (
        db.query(PathRun)
        .join(Device, Device.id == PathRun.device_id)
        .filter(
            Device.ip_address == source_ip,
            PathRun.destination_ip == destination_ip,
            PathRun.executed_at >= time_threshold
        )
        .order_by(PathRun.executed_at.asc())
        .all()
    )

    history = []

    for run in runs:
        hops = db.query(PathHop).filter(PathHop.run_id == run.id).all()

        if not hops:
            continue

        latencies = [h.latency_avg for h in hops if h.latency_avg is not None]

        avg_latency = sum(latencies) / len(latencies) if latencies else None
        packet_loss = max(h.packet_loss_percent for h in hops)

        history.append({
            "timestamp": run.executed_at,
            "latency": round(avg_latency, 2) if avg_latency else None,
            "packet_loss": packet_loss,
            "availability": 100 - packet_loss
        })

    return history


# ==========================================================
# FINAL COMBINED API (PATH + HISTORY)
# ==========================================================
def get_path_analysis_with_history(
    db,
    source_ip: str,
    destination_ip: str,
    device_id: int | None = None
):

    traceroute_data = execute_traceroute(
        db=db,
        device_id=device_id,
        device_name=None,
        device_ip=source_ip,
        destination_ip=destination_ip
    )

    formatted_path = format_path_response(traceroute_data)

    history = get_path_history(
        db,
        source_ip=source_ip,
        destination_ip=destination_ip
    )

    return {
        "path_analysis": formatted_path,
        "path_history": history
    }     

