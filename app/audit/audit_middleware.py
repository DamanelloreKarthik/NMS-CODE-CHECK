
# from fastapi import Request
# from starlette.middleware.base import BaseHTTPMiddleware
# from app.audit.audit_services import create_audit_log
# from app.core.database import SessionLocal
# import logging

# logger = logging.getLogger(__name__)


# SKIP_PATHS = [
#     "/docs",
#     "/openapi.json",
#     "/redoc",
# ]


# SKIP_PREFIXES = [
#     "/auth",            
#     "/users",           
#     "/api/audit/logs",  
# ]

# class AuditMiddleware(BaseHTTPMiddleware):

#     async def dispatch(self, request: Request, call_next):
#         response = await call_next(request)

#         path = request.url.path

      
#         if (
#             path in SKIP_PATHS
#             or any(path.startswith(prefix) for prefix in SKIP_PREFIXES)
#         ):
#             return response

#         db = SessionLocal()

#         try:
           
#             user = getattr(request.state, "user", None)

#             username = getattr(user, "email", "Anonymous")
#             user_id = getattr(user, "id", None)

#             create_audit_log(
#                 db=db,
#                 log_type="SYSTEM",
#                 user_id=user_id,
#                 username=username,
#                 module="System",
#                 action=request.method,
#                 resource_type="API",
#                 resource_id=path,
#                 status="SUCCESS" if response.status_code < 400 else "FAILED",
#                 description=f"{username} performed {request.method} on {path}",
#                 remote_ip=request.client.host if request.client else None,
#                 # user_agent=request.headers.get("user-agent"),
#             )

#         except Exception as e:
#             logger.error(f"AUDIT LOG FAILED: {e}")

#         finally:
#             db.close()

#         return response





# from fastapi import Request
# from starlette.middleware.base import BaseHTTPMiddleware
# from app.audit.audit_services import create_audit_log
# from app.core.database import SessionLocal
# import logging

# logger = logging.getLogger(__name__)

# SKIP_PATHS = [
#     "/docs",
#     "/openapi.json",
#     "/redoc",
# ]

# SKIP_PREFIXES = [
#     "/auth",
#     "/users",
#     "/api/audit/logs",
# ]


# class AuditMiddleware(BaseHTTPMiddleware):

#     async def dispatch(self, request: Request, call_next):

#         response = await call_next(request)

#         path = request.url.path

#         if (
#             path in SKIP_PATHS
#             or any(path.startswith(prefix) for prefix in SKIP_PREFIXES)
#         ):
#             return response

#         db = SessionLocal()

#         try:

#             user = getattr(request.state, "user", None)

#             username = getattr(user, "email", "Anonymous")
#             user_id = getattr(user, "id", None)

#             create_audit_log(
#                 db=db,
#                 module="SYSTEM",
#                 action=request.method,
#                 status="SUCCESS" if response.status_code < 400 else "FAILED",
#                 username=username,
#                 user_id=user_id,
#                 request=request,
#                 resource_type="API",
#                 resource_id=path,
#                 description=f"{username} performed {request.method} on {path}",
#             )

#         except Exception as e:
#             logger.error(f"AUDIT LOG FAILED: {e}")

#         finally:
#             db.close()

#         return response


# from fastapi import Request
# from starlette.middleware.base import BaseHTTPMiddleware
# from app.audit.audit_services import create_audit_log
# from app.core.database import SessionLocal
# import logging

# logger = logging.getLogger(__name__)

# # Paths to skip completely
# SKIP_PATHS = [
#     "/docs",
#     "/openapi.json",
#     "/redoc",
# ]

# # Prefixes to skip
# SKIP_PREFIXES = [
#     "/auth",
#     "/api/audit/logs",
# ]


# class AuditMiddleware(BaseHTTPMiddleware):

#     async def dispatch(self, request: Request, call_next):

#         response = await call_next(request)

#         path = request.url.path
#         method = request.method

#         # ✅ Skip unwanted routes
#         if path in SKIP_PATHS or any(path.startswith(p) for p in SKIP_PREFIXES):
#             return response

#         # ✅ IMPORTANT: Skip write operations to avoid duplicate logs
#         if method in ["POST", "PUT", "PATCH", "DELETE"]:
#             return response

#         db = SessionLocal()

#         try:
#             user = getattr(request.state, "user", None)

#             username = getattr(user, "email", "Anonymous")
#             user_id = getattr(user, "id", None)

#             # Optional: skip anonymous logs
#             if username == "Anonymous":
#                 return response

#             create_audit_log(
#                 db=db,
#                 module="SYSTEM",
#                 action="VIEW",
#                 status="SUCCESS" if response.status_code < 400 else "FAILED",
#                 user_id=user_id,
#                 username=username,
#                 request=request,
#                 resource_type="API",
#                 resource_id=path,
#                 description=f"{username} viewed {path}",
#             )

#         except Exception as e:
#             logger.error(f"AUDIT MIDDLEWARE FAILED: {e}")

#         finally:
#             db.close()

#         return response




# from fastapi import Request
# from starlette.middleware.base import BaseHTTPMiddleware
# from app.audit.audit_services import create_audit_log
# from app.core.database import SessionLocal
# import logging

# logger = logging.getLogger(__name__)

# # Paths to skip completely
# SKIP_PATHS = [
#     "/docs",
#     "/openapi.json",
#     "/redoc",
# ]

# # Prefixes to skip
# SKIP_PREFIXES = [
#     "/auth",
#     "/api/audit/logs",
# ]


# class AuditMiddleware(BaseHTTPMiddleware):

#     async def dispatch(self, request: Request, call_next):

#         response = await call_next(request)

#         path = request.url.path
#         method = request.method

#         # ❌ Skip only docs + audit APIs
#         if path in ["/docs", "/openapi.json", "/redoc"] or path.startswith("/api/audit"):
#             return response

#         db = SessionLocal()

#         try:
#             user = getattr(request.state, "user", None)

#             username = getattr(user, "email", "Anonymous")
#             user_id = getattr(user, "id", None)

#             # ✅ Dynamic module detection
#             if "/users" in path:
#                 module = "USERS"
#             elif "/roles" in path:
#                 module = "ROLES"
#             elif "/permissions" in path:
#                 module = "PERMISSIONS"
#             elif "/auth" in path:
#                 module = "AUTH"
#             else:
#                 module = "SYSTEM"

#             create_audit_log(
#                 db=db,
#                 module=module,
#                 action=method,
#                 status="SUCCESS" if response.status_code < 400 else "FAILED",
#                 user_id=user_id,
#                 username=username,
#                 request=request,
#                 resource_type="API",
#                 resource_id=path,
#                 description=f"{username} performed {method} on {path}",
#             )

#         except Exception as e:
#             logger.error(f"AUDIT FAILED: {e}")

#         finally:
#             db.close()

#         return response


from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.audit.audit_services import create_audit_log, build_description
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

# Skip docs & audit paths
# SKIP_PATHS = ["/docs", "/openapi.json", "/redoc"]
SKIP_PATHS = [
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/audit/logs/analytics",
    "/api/audit/logs/module-distribution",
    "/api/audit/logs/user-activity",
    "/api/audit/logs/top-conversations",
]

# SKIP_PREFIXES = ["/api/audit/logs"]
SKIP_PREFIXES=[]


# Paths that already manually log to avoid duplicates
MANUAL_LOG_PATHS = [
    "/auth/login",
    "/auth/register",
    "/auth/refresh-token",
    
    
]

class AuditMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        path = request.url.path
        method = request.method

        # Skip docs, audit logs, or paths that are manually logged
        if (
            path in SKIP_PATHS
            or any(path.startswith(prefix) for prefix in SKIP_PREFIXES)
            or any(path.startswith(manual) for manual in MANUAL_LOG_PATHS)
        ):
            return response

        db = SessionLocal()
        try:
            user = getattr(request.state, "user", None)
            # username = getattr(user, "email", "Anonymous")
            username = getattr(user, "email", None) or getattr(user, "username", None) or "SYSTEM"
            user_id = getattr(user, "id", None)

            # Detect module
            if "/users" in path:
                module = "USERS"
            elif "/roles" in path:
                module = "ROLES"
            elif "/permissions" in path:
                module = "PERMISSIONS"
            elif "/auth" in path:
                module = "AUTH"
            else:
                module = "SYSTEM"

            # Build description
            description = build_description(username, method, path)
            

            # Create audit log automatically
            create_audit_log(
                db=db,
                module=module,
                action=method,
                status="SUCCESS" if response.status_code < 400 else "FAILED",
                user_id=user_id,
                username=username,
                request=request,
                resource_type="API",
                resource_id=path,
                description=description,
            )

        except Exception as e:
            logger.error(f"AUDIT FAILED: {e}")
        finally:
            db.close()

        return response


