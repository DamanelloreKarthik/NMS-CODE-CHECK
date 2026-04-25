
# from fastapi import Request
# from sqlalchemy.orm import Session
# from app.audit.audit_model import AuditLog


# def get_client_ip(request: Request | None) -> str | None:
#     if not request:
#         return None

#     forwarded = request.headers.get("x-forwarded-for")
#     if forwarded:
#         return forwarded.split(",")[0].strip()

#     if request.client:
#         return request.client.host

#     return None


# def create_audit_log(
#     db: Session,
#     *,
#     module: str,
#     action: str,
#     status: str,
#     user_id: int | None = None,
#     username: str | None = None,
#     request: Request | None = None,
#     resource_type: str | None = None,
#     resource_id: str | None = None,
#     old_value: str | None = None,
#     new_value: str | None = None,
#     description: str | None = None,
# ):
#     log = AuditLog(
#         user_id=user_id,
#         username=username,
#         module=module,
#         log_type=module,
#         action=action,
#         resource_type=resource_type,
#         resource_id=resource_id,
#         old_value=old_value,
#         new_value=new_value,
#         status=status,
#         remote_ip=get_client_ip(request),
#         # user_agent=request.headers.get("user-agent") if request else None,
#         description=description,
#     )

#     db.add(log)
#     db.commit()
#     db.refresh(log)

#     return log



# from fastapi import Request
# from sqlalchemy.orm import Session
# from app.audit.audit_model import AuditLog


# # ✅ Get Client IP
# def get_client_ip(request: Request | None) -> str | None:
#     if not request:
#         return None

#     forwarded = request.headers.get("x-forwarded-for")
#     if forwarded:
#         return forwarded.split(",")[0].strip()

#     if request.client:
#         return request.client.host

#     return None


# # ✅ Map HTTP → Operation (UI friendly)
# def map_operation(method: str) -> str:
#     return {
#         "GET": "VIEW",
#         "POST": "CREATE",
#         "PUT": "UPDATE",
#         "DELETE": "DELETE"
#     }.get(method, method)


# # ✅ Detect module from path
# def get_module(path: str) -> str:
#     if path.startswith("/users"):
#         return "USERS"
#     if path.startswith("/roles"):
#         return "ROLES"
#     if path.startswith("/permissions"):
#         return "PERMISSIONS"
#     return "SYSTEM"


# # ✅ Build readable message
# def build_description(username: str, method: str, path: str) -> str:

#     if path.startswith("/users"):
#         if method == "GET":
#             return f"{username} viewed users list"
#         elif method == "POST":
#             return f"{username} created a user"
#         elif method == "PUT":
#             return f"{username} updated a user"
#         elif method == "DELETE":
#             return f"{username} deleted a user"

#     if path.startswith("/roles"):
#         return f"{username} accessed roles"

#     return f"{username} performed {method} on {path}"


# # ✅ Main function (NO CHANGE in signature)
# def create_audit_log(
#     db: Session,
#     *,
#     module: str,
#     action: str,
#     status: str,
#     user_id: int | None = None,
#     username: str | None = None,
#     request: Request | None = None,
#     resource_type: str | None = None,
#     resource_id: str | None = None,
#     old_value: str | None = None,
#     new_value: str | None = None,
#     description: str | None = None,
# ):
#     log = AuditLog(
#         user_id=user_id,
#         username=username,
#         module=module,
#         log_type=module,
#         action=action,
#         resource_type=resource_type,
#         resource_id=resource_id,
#         old_value=old_value,
#         new_value=new_value,
#         status=status,
#         remote_ip=get_client_ip(request),
#         description=description,
#     )

#     db.add(log)
#     db.commit()
#     db.refresh(log)

#     return log


from fastapi import Request
from sqlalchemy.orm import Session
from app.audit.audit_model import AuditLog

# ✅ Get Client IP
def get_client_ip(request: Request | None) -> str | None:
    if not request:
        return None

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    if request.client:
        return request.client.host

    return None

# ✅ Map HTTP → Operation
def map_operation(method: str) -> str:
    return {
        "GET": "VIEW",
        "POST": "CREATE",
        "PUT": "UPDATE",
        "DELETE": "DELETE"
    }.get(method, method)

# ✅ Detect module from path
def get_module(path: str) -> str:
    if path.startswith("/users"):
        return "USERS"
    if path.startswith("/roles"):
        return "ROLES"
    if path.startswith("/permissions"):
        return "PERMISSIONS"
    if path.startswith("/auth"):
        return "AUTH"
    return "SYSTEM"

# ✅ Build readable message
def build_description(username: str, method: str, path: str) -> str:
    if path.startswith("/users"):
        if method == "GET":
            return f"{username} viewed users list"
        elif method == "POST":
            return f"{username} created a user"
        elif method == "PUT":
            return f"{username} updated a user"
        elif method == "DELETE":
            return f"{username} deleted a user"

    if path.startswith("/roles"):
        return f"{username} accessed roles"

    if path.startswith("/auth"):
        return f"{username} performed auth operation"

    return f"{username} performed {method} on {path}"

# ✅ Main function to create audit log
def create_audit_log(
    db: Session,
    *,
    module: str,
    action: str,
    status: str,
    user_id: int | None = None,
    username: str | None = None,
    request: Request | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
    description: str | None = None,
):
    log = AuditLog(
        user_id=user_id,
        username=username,
        module=module,
        log_type=module,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
        status=status,
        remote_ip=get_client_ip(request),
        description=description,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log