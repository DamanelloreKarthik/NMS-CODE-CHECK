from app.db_utils import safe_commit
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import ipaddress
from database import get_db
from app.path_analysis.schemas import (
    DeviceCreateRequest,
    DeviceResponse
)
from app.core.security import require_api_key
from app.path_analysis.services import (
    build_dynamic_destination_candidates,
    analyze_network_path_with_context
)
from app.path_analysis.device_reg import register_device


# ROUTER INIT


router = APIRouter()



# DEVICE REGISTRATION 


@router.post("/", response_model=DeviceResponse, dependencies=[Depends(require_api_key)])
def create_device(request: DeviceCreateRequest, db: Session = Depends(get_db)):
    try:
        return register_device(db, request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/full", dependencies=[Depends(require_api_key)])
def get_full_analysis(
    source_ip: str = Query(..., pattern=r"^\d{1,3}(\.\d{1,3}){3}$"),
    destination_ip: str = Query(..., pattern=r"^\d{1,3}(\.\d{1,3}){3}$"),
    db: Session = Depends(get_db)
):
    """
    - Destination dropdown
    - Path analysis
    - Path history
    """

    try:
        
        ipaddress.ip_address(source_ip)
        ipaddress.ip_address(destination_ip)

        # DESTINATIONS (dropdown)

        destinations = build_dynamic_destination_candidates(db, source_ip)

        # PATH + HISTORY
    
        analysis = analyze_network_path_with_context(
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