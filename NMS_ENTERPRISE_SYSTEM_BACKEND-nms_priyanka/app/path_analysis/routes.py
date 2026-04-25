
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db

from app.path_analysis.schemas import (
    DeviceCreateRequest,
    DeviceResponse
)
from app.core.security import require_api_key
from app.path_analysis.services import (
    get_destination_options,
    get_path_analysis_with_history
)

from app.path_analysis.device_reg import register_device


# =====================================================
# ROUTER INIT
# =====================================================

router = APIRouter()


# =====================================================
# DEVICE REGISTRATION (KEEP SAME)
# =====================================================

@router.post("/", response_model=DeviceResponse, dependencies=[Depends(require_api_key)])
def create_device(request: DeviceCreateRequest, db: Session = Depends(get_db)):
    try:
        return register_device(db, request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =====================================================
# ✅ SINGLE API FOR FULL SCREEN (IMPORTANT)
# =====================================================

@router.get("/full", dependencies=[Depends(require_api_key)])
def get_full_analysis(
    source_ip: str,
    destination_ip: str,
    db: Session = Depends(get_db)
):
    """
    🔥 Single API for entire screen:
    - Destination dropdown
    - Path analysis
    - Path history
    """

    try:
        # -----------------------------
        # DESTINATIONS (dropdown)
        # -----------------------------
        destinations = get_destination_options(db, source_ip)

        # -----------------------------
        # PATH + HISTORY
        # -----------------------------
        analysis = get_path_analysis_with_history(
            db,
            source_ip,
            destination_ip
        )

        return {
            "filters": {
                "source_ip": source_ip,
                "destination_ip": destination_ip
            },
            "destinations": destinations,
            "path_analysis": analysis.get("path_analysis"),
            "path_history": analysis.get("path_history")
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

