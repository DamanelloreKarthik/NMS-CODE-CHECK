
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List


from app.core.database import get_db
from app.models.user import Role, User 
from app.roles.role_schema import RoleCreate, RoleOut

router = APIRouter(prefix="/roles", tags=["Roles Management"])


@router.get("/", response_model=List[RoleOut])
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    for r in roles:
      
        r.user_count = db.query(User).filter(User.role_id == r.id).count()
    return roles


@router.post("/", response_model=RoleOut)
def create_role(role_data: RoleCreate, db: Session = Depends(get_db)):
    if db.query(Role).filter(Role.name == role_data.name).first():
        raise HTTPException(status_code=400, detail="Role name already exists")
    
    new_role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions_metadata=role_data.permissions_metadata # Matches your Tree structure
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


@router.put("/{role_id}", response_model=RoleOut)
def update_role(role_id: UUID, role_update: RoleCreate, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    role.name = role_update.name
    role.description = role_update.description
    role.permissions_metadata = role_update.permissions_metadata
    
    db.commit()
    db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: UUID, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    db.delete(role)
    db.commit()
    return None