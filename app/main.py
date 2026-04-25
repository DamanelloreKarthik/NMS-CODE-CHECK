
from fastapi import FastAPI
from app.core.database import Base, engine
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.users.user_router import router as user_router
from app.auth.auth_router import router as auth_router
from app.roles.role_router import router as role_router
from fastapi.middleware.cors import CORSMiddleware
from app.audit.audit_router import router as audit_router
from app.audit.audit_middleware import AuditMiddleware
from app.core.permissions_router import router as permission_router

from app.users.user_profile_router import router as user_profile_router
from app.users.pat_router import router as pat_router


app = FastAPI(title="NMS RBAC Backend")
Base.metadata.create_all(bind=engine)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(role_router)
app.include_router(permission_router)

app.add_middleware(AuditMiddleware)

app.include_router(audit_router)

app.include_router(user_profile_router)

app.include_router(pat_router)


