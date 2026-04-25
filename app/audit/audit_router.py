
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.audit.audit_model import AuditLog

router = APIRouter(
    prefix="/api/audit/logs",
    tags=["Audit Logs"]
)


@router.get("/overview")
def audit_overview(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    module: str | None = None,
    status: str | None = None,
    search: str | None = None,
):

    query = db.query(AuditLog)

    if module:
        query = query.filter(func.lower(AuditLog.module) == module.lower())

    if status:
        query = query.filter(func.lower(AuditLog.status) == status.lower())

    if search:
        query = query.filter(AuditLog.description.ilike(f"%{search}%"))

    total = query.count()

    logs = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    table_data = [
        {
            "id": log.id,
            "timestamp": log.created_at,
            "module": log.module,
            "operation": log.action,
            "user": log.username,
            "ip": log.remote_ip,
            "message": log.description,
            "status": log.status,
        }
        for log in logs
    ]


    total_events = db.query(AuditLog).count()

    failures = db.query(AuditLog).filter(
        AuditLog.status == "FAILED"
    ).count()

    success = total_events - failures
    success_rate = (success / total_events * 100) if total_events else 0

    timeline_logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )

    timeline = [
        {
            "time": log.created_at.strftime("%H:%M"),
            "count": 1
        }
        for log in timeline_logs
    ]


    module_results = (
        db.query(AuditLog.module, func.count(AuditLog.id))
        .group_by(AuditLog.module)
        .all()
    )

    module_total = sum(count for _, count in module_results)

    module_distribution = [
        {
            "module": module,
            "percentage": round((count / module_total) * 100, 2) if module_total else 0
        }
        for module, count in module_results
    ]

 
    user_results = (
        db.query(AuditLog.username, func.count(AuditLog.id))
        .group_by(AuditLog.username)
        .order_by(func.count(AuditLog.id).desc())
        .all()
    )

    user_activity = [
        {
            "user": (
                "System" if not username or username == "SYSTEM"
                else username.split("@")[0].capitalize()
            ),
            "count": count
        }
        for username, count in user_results
    ]

    top_logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )

    top_conversations = [
        {
            "timestamp": log.created_at,
            "module": log.module,
            "operation": log.action,
            "user": log.username or "SYSTEM",
            "remote_ip": log.remote_ip,
            "message": log.description,
            "status": log.status,
        }
        for log in top_logs
    ]

    return {
        "analytics": {
            "total_events": total_events,
            "success_rate": round(success_rate, 2),
            "failures": failures,
            "timeline": timeline,
        },
        "module_distribution": module_distribution,
        "user_activity": user_activity,
        "top_conversations": top_conversations,
        "logs_table": {
            "total": total,
            "data": table_data
        }
    }