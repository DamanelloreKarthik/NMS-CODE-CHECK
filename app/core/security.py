from app.db_utils import safe_commit
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import os

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
VALID_API_KEY = os.getenv("API_KEY")

def require_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key"
        )