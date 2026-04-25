
from pydantic import BaseModel, field_validator, SecretStr
from typing import List, Optional
from datetime import datetime
import ipaddress

# =====================================================
# DEVICE CREATE REQUEST
# =====================================================

class DeviceCreateRequest(BaseModel):
    name: str
    ip_address: str
    category: str

    username: str
    password: SecretStr   # ✅ FIXED (masked in logs)


# =====================================================
# DEVICE RESPONSE
# =====================================================

class DeviceResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    category: str

    class Config:
        from_attributes = True


# =====================================================
# REQUEST
# =====================================================

class PathTraceRequest(BaseModel):
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    device_ip: Optional[str] = None

    destination_ip: str
    port: Optional[int] = None

    # ✅ ADDED VALIDATION
    @field_validator("destination_ip")
    @classmethod
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError("Must be a valid IP address")
        return v


# =====================================================
# HOP RESPONSE
# =====================================================

class PathHopResponse(BaseModel):
    hop_number: int
    ip_address: Optional[str]
    latency_min: Optional[float]
    latency_avg: Optional[float]
    latency_max: Optional[float]
    packet_loss_percent: Optional[float]


# =====================================================
# MAIN RESPONSE
# =====================================================

class PathTraceResponse(BaseModel):
    run_id: int
    device_name: str
    device_ip: str
    destination_ip: str
    executed_at: datetime
    hops: List[PathHopResponse]