# from pydantic import BaseModel
# from uuid import UUID
# from typing import Optional, List


# class RoleCreate(BaseModel):
#     name: str
#     description: Optional[str] = None
#     permission_ids: List[UUID] = []


# class RoleOut(BaseModel):
#     id: UUID
#     name: str
#     description: Optional[str]

#     class Config:
#         from_attributes = True


from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List, Dict, Any

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    # Use a Dict to capture the tree structure from the checkboxes
    # Example: {"Monitoring": {"read": true, "write": false}, "Visualization": {...}}
    permissions_metadata: Dict[str, Any] 

class RoleOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    user_count: int = 0  # This matches your "USER COUNT" column
    # Optional: include the metadata if you need to edit the role later
    permissions_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True