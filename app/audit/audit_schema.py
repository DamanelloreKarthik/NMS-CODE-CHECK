
from pydantic import BaseModel
from datetime import datetime

class AuditLogUI(BaseModel):
    id: int
    timestamp: datetime
    log_type: str
    user_name: str | None
    
    status: str
    description: str | None
    system_ip: str | None