
from app.db_utils import safe_commit
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Optional
from datetime import datetime, timedelta
from app.core.security import require_api_key
from database import get_db
from app.syslog.models import Syslog
from app.syslog.intelligence import detect_brute_force, detect_unusual_activity

router = APIRouter(
    prefix="/api/log-management",
    tags=["Log Management"],
    dependencies=[Depends(require_api_key)]
)


# TIME RANGE HANDLER

def resolve_time_range(time_range: Optional[str]):
    now = datetime.now()

    if time_range == "last_hour":
        return now - timedelta(hours=1), now

    elif time_range == "last_24_hours":
        return now - timedelta(hours=24), now

    elif time_range == "today":
        start = datetime(now.year, now.month, now.day)
        return start, now

    return None, None


# COMMON FILTER ENGINE

def apply_filters(query, severity, device_ip, search, start_time, end_time):

    if severity and severity.lower() != "all":
        query = query.filter(Syslog.severity.ilike(severity))

    if device_ip:
        query = query.filter(Syslog.host == device_ip)

    if search:
        query = query.filter(
            (Syslog.message.ilike(f"%{search}%")) |
            (Syslog.hostname.ilike(f"%{search}%")) |
            (Syslog.host.ilike(f"%{search}%"))
        )

    if start_time:
        query = query.filter(Syslog.timestamp >= start_time)

    if end_time:
        query = query.filter(Syslog.timestamp <= end_time)

    return query


@router.get("/dashboard", dependencies=[Depends(require_api_key)])
def build_security_event_timeline(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=500),
    severity: Optional[str] = "all",
    device_ip: Optional[str] = None,
    time_range: Optional[str] = "last_24_hours",
    search: Optional[str] = None,
    interval: str = Query("hour", pattern="^(minute|hour|day)$"),
    db: Session = Depends(get_db)
):

    start_time, end_time = resolve_time_range(time_range)

    # BASE QUERY WITH FILTERS
    base_query = db.query(Syslog)
    base_query = apply_filters(
        base_query, severity, device_ip, search, start_time, end_time
    )

    # EVENT TABLE DATA
    total = base_query.count()

    logs = (
        base_query.order_by(Syslog.timestamp.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    events = []
    for log in logs:

        category = None
        if log.tags and log.tags.get("event_type"):
            category = log.tags.get("event_type")
        elif "Event|" in log.raw:
            category = "LOG"

        events.append({
            "id": log.id,
            "timestamp": log.timestamp,
            "severity": log.severity,
            "source": log.host,
            "hostname": log.hostname,
            "message": log.message,
            "category": category
        })

    # PERFORMANCE METRICS
    total_logs = total

    last_min_start = datetime.utcnow() - timedelta(minutes=5)

    eps_query = db.query(Syslog)
    eps_query = apply_filters(
        eps_query, severity, device_ip, search,
        last_min_start, datetime.utcnow()
    )

    logs_last_window = eps_query.count()

    # Stable EPS (5 min window)
    events_per_second = round(logs_last_window / 300, 2) if logs_last_window else 0

    # DB Size
    db_size_query = text("SELECT pg_database_size(current_database());")
    size_bytes = db.execute(db_size_query).scalar()
    storage_usage_gb = round(size_bytes / (1024**3), 2)

    performance = {
        "events_per_second": events_per_second,
        "total_volume": total_logs,
        "storage_usage_gb": storage_usage_gb
    }

    # ANALYTICS GRAPH
    if interval == "minute":
        trunc = "minute"
        label = "%H:%M"
    elif interval == "day":
        trunc = "day"
        label = "%Y-%m-%d"
    else:
        trunc = "hour"
        label = "%H:00"

    analytics_query = db.query(
        func.date_trunc(trunc, Syslog.timestamp).label("bucket"),
        func.count(Syslog.id)
    )

    analytics_query = apply_filters(
        analytics_query, severity, device_ip, search, start_time, end_time
    )

    analytics_results = (
        analytics_query.group_by("bucket")
        .order_by("bucket")
        .all()
    )

    analytics = [
        {
            "time": row.bucket.strftime(label),
            "count": row[1]
        }
        for row in analytics_results
    ]

    full_logs = base_query.all()

    attackers = detect_brute_force(full_logs)
    unusual = detect_unusual_activity(full_logs)

    return {
        "filters": {
            "severity": severity,
            "device_ip": device_ip,
            "time_range": time_range,
            "search": search
        },
        "events": {
            "total": total,
            "page": page,
            "limit": limit,
            "data": events
        },
        "performance": performance,
        "analytics": analytics,
        "security_insights": {
            "possible_brute_force_ips": attackers,
            "unusual_activity_detected": unusual
        },
        "log_spike_detected": detect_log_spike(db, device_ip) if device_ip else False
    }


# Log Anomaly Detection

def detect_log_spike(db, device_ip):
    last_5_min = datetime.utcnow() - timedelta(minutes=5)
    prev_5_min = datetime.utcnow() - timedelta(minutes=10)

    recent = db.query(Syslog).filter(
        Syslog.host == device_ip,
        Syslog.timestamp >= last_5_min
    ).count()

    previous = db.query(Syslog).filter(
        Syslog.host == device_ip,
        Syslog.timestamp >= prev_5_min,
        Syslog.timestamp < last_5_min
    ).count()

    if previous == 0:
        return False

    return recent > previous * 2