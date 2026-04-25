
import secrets
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.personal_access_token import PersonalAccessToken
from app.models.user import User
from app.users.pat_schema import PATCreate, PATOut, PATPaginationResponse

router = APIRouter(
    prefix="/personal-access-tokens",
    tags=["Personal Access Tokens"]
)


@router.post("/", response_model=PATOut)
def create_pat(data: PATCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.utcnow()
    expiry_date = now + timedelta(days=data.validity_days)

    token_value = f"pat_{secrets.token_hex(16)}"

    new_token = PersonalAccessToken(
        name=data.name,
        description=data.description,
        token=token_value,
        user_id=data.user_id,
        created_by="admin", 
        created_at=now,
        expires_at=expiry_date
    )

    db.add(new_token)
    db.commit()
    db.refresh(new_token)

    new_token.user_name = user.username 
    return new_token


@router.get("/", response_model=PATPaginationResponse)
def list_pats(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1)
):
    offset = (page - 1) * page_size
    
    query = db.query(PersonalAccessToken, User.username).join(
        User, PersonalAccessToken.user_id == User.id
    )
    
    total = query.count()
    results = query.offset(offset).limit(page_size).all()

    items = []
  
    current_time = datetime.utcnow() 

    for pat, username in results:
      
        is_active_status = False
        if pat.expires_at:
            is_active_status = pat.expires_at > current_time

        items.append(PATOut(
            id=pat.id,
            name=pat.name,
            description=pat.description or "",
            user_name=username,          
            token="********",            
            created_by=pat.created_by,   
            created_at=pat.created_at,   
            expires_at=pat.expires_at,   
            is_active=is_active_status 
        ))

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pat(token_id: UUID, db: Session = Depends(get_db)):
    token = db.query(PersonalAccessToken).filter(PersonalAccessToken.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    db.delete(token)
    db.commit()
    return None