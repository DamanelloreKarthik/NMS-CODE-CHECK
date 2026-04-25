
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import Permission, RolePermission, Role

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"]
)


@router.get("/")
def list_permissions(db: Session = Depends(get_db)):
    permissions = db.query(Permission).all()
    return permissions

