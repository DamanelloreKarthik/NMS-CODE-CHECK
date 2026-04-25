
from datetime import datetime, timezone
import re
import logging

logger = logging.getLogger(__name__)

# =========================================================
# RFC STANDARD MAPS
# =========================================================
SEVERITY_MAP = {
    0: "EMERGENCY",
    1: "ALERT",
    2: "CRITICAL",
    3: "ERROR",
    4: "WARNING",
    5: "NOTICE",
    6: "INFO",
    7: "DEBUG",
}

FACILITY_MAP = {
    0: "kernel", 1: "user", 2: "mail", 3: "daemon",
    4: "auth", 5: "syslog", 6: "lpr", 7: "news",
    8: "uucp", 9: "clock", 10: "authpriv", 11: "ftp",
    16: "local0", 17: "local1", 18: "local2",
    19: "local3", 20: "local4", 21: "local5",
    22: "local6", 23: "local7",
}

def parse_syslog(raw: str, source_ip: str):
    raw = raw.strip()

    severity = "INFO"
    facility = None
    hostname = None
    app_name = None
    process = None
    tags = {}

    message = raw

    pri_match = re.match(r"<(\d+)>", raw)
    if pri_match:
        pri = int(pri_match.group(1))
        severity = SEVERITY_MAP.get(pri % 8, "INFO")
        facility = FACILITY_MAP.get(pri // 8, str(pri // 8))

    rfc5424_match = re.match(r"<\d+>(\d+)\s+(.*)", raw)

    if rfc5424_match:
        try:
            parts = rfc5424_match.group(2).split()

            if len(parts) >= 7:
                timestamp_str = parts[0]
                hostname = parts[1]
                app_name = parts[2]
                process = parts[3]

                if " - - " in raw:
                    message = raw.split(" - - ", 1)[-1]
                else:
                    message = " ".join(parts[6:])

        except Exception as exc:
            logger.warning("RFC5424 parse failed for message %.80r: %s", raw, exc)

    else:
        rfc3164 = re.match(
            r"<\d+>\s*(\w{3}\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(.*)",
            raw
        )
        if rfc3164:
            hostname = rfc3164.group(2)
            message = rfc3164.group(3)

    pipe_match = re.search(r"Event\|(\d+)\|(\w+)\|\|\|(.*)", message)

    if pipe_match:
        tags["event_id"] = pipe_match.group(1)
        tags["event_type"] = pipe_match.group(2)
        message = pipe_match.group(3).strip()

    user_match = re.search(r"\bby\s+(\w+)", message, re.IGNORECASE)
    if user_match:
        tags["user"] = user_match.group(1)

    ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", message)
    if ip_match:
        tags["src_ip"] = ip_match.group(1)

    upper = message.upper()

    if "LOGIN" in upper:
        tags["event_type"] = "LOGIN"
    elif "LOGOUT" in upper:
        tags["event_type"] = "LOGOUT"

    if "WINDOWS" in upper:
        os_type = "windows"
        device_type = "server"
    elif "VMWARE" in upper or "ESXI" in upper:
        os_type = "esxi"
        device_type = "hypervisor"
    else:
        os_type = "network"
        device_type = "network-device"

    if not hostname:
        hostname = source_ip

    event_time = None

    ts_match = re.match(
        r"<\d+>\d\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
        raw
    )
    if ts_match:
        try:
            event_time = datetime.fromisoformat(ts_match.group(1))
        except Exception as exc:
            logger.warning("RFC5424 timestamp parse failed %.80r: %s", raw, exc)

    if not event_time:
        ts_match = re.match(
            r"<\d+>\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+"
            r"(\d+)\s+(\d{2}:\d{2}:\d{2})",
            raw
        )
        if ts_match:
            try:
                current_year = datetime.now(timezone.utc).year
                event_time = datetime.strptime(
                    f"{ts_match.group(1)} {ts_match.group(2)} {current_year} {ts_match.group(3)}",
                    "%b %d %Y %H:%M:%S"
                )
            except Exception as exc:
                logger.warning("RFC3164 timestamp parse failed %.80r: %s", raw, exc)

    if not event_time:
        event_time = datetime.now(timezone.utc)

    return {
        "timestamp": event_time,
        "received_at": datetime.now(),
        "host": source_ip,
        "hostname": hostname,
        "message": message.strip(),
        "raw": raw,
        "severity": severity,
        "facility": facility,
        "os_type": os_type,
        "device_type": device_type,
        "app_name": app_name,
        "process": process,
        "protocol": "udp",
        "source_port": None,
        "tags": tags,
    }