
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import get_db
from app.flows import crud
from app.core.security import require_api_key

router = APIRouter(
    prefix="/flow",
    tags=["Flow Dashboard"],
    dependencies=[Depends(require_api_key)]
)




# -------------------------
# DASHBOARD API
# -------------------------
@router.get("/dashboard", dependencies=[Depends(require_api_key)])
def get_dashboard(
    minutes: int = Query(60, ge=1),
    event_source: str | None = None,
    interface: str | None = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=minutes)

    return crud.get_dashboard(
        db=db,
        start_time=start_time,
        end_time=end_time,
        event_source=event_source,
        interface=interface,
        limit=limit
    )


# -----------------------------
# EXPLORER API
# -----------------------------
@router.get("/explorer", dependencies=[Depends(require_api_key)])
def explorer(
    minutes: int = Query(60, ge=1),
    event_source: str = None,
    interface: int = None,
    source_ip: str = None,
    destination_ip: str = None,
    port: int = None,
    protocol: str = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=minutes)

    return crud.get_explorer(
        db=db,
        start_time=start_time,
        end_time=end_time,
        event_source=event_source,
        interface=interface,
        source_ip=source_ip,
        destination_ip=destination_ip,
        port=port,
        protocol=protocol,
        limit=limit
    )


# -------------------------
# ANALYTICS API
# -------------------------
@router.get("/analytics", dependencies=[Depends(require_api_key)])
def analytics(
    minutes: int = Query(60, ge=1),
    event_source: str | None = None,
    interface: str | None = None,
    db: Session = Depends(get_db)
):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=minutes)

    return crud.get_analytics(
        db=db,
        start_time=start_time,
        end_time=end_time,
        event_source=event_source,
        interface=interface
    )