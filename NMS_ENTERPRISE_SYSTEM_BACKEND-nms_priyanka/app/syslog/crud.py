from sqlalchemy.orm import Session ,or_, func
from app.syslog.models import Syslog

def insert_syslog(db: Session, data: dict):
    log = Syslog(
        timestamp=data["timestamp"],
        host=data["host"],
        hostname=data.get("hostname"),
        app_name=data.get("app_name"),
        process=data.get("process"),
        message=data["message"],
        raw=data["raw"],             
        severity=data.get("severity"),
        facility=data.get("facility"),
        os_type=data.get("os_type"),
        device_type=data.get("device_type"),
        protocol=data.get("protocol"),
        source_port=data.get("source_port"),
        tags=data.get("tags", {})
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def search_logs(db: Session, query: str, limit: int = 100):
    q = query.strip()

    return (
        db.query(Syslog)
        .filter(
            or_(
                Syslog.message.ilike(f"%{q}%"),
                Syslog.raw.ilike(f"%{q}%"),
                Syslog.severity.ilike(q),        # INFO, NOTICE, ERROR
                Syslog.facility.ilike(q),        # local0, auth
                Syslog.hostname.ilike(f"%{q}%"),
                Syslog.host.ilike(f"%{q}%")
            )
        )
        .order_by(Syslog.timestamp.desc())
        .limit(limit)
        .all()
    )

