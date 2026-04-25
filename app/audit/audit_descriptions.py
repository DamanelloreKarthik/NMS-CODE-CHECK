# app/audit/audit_descriptions.py

from fastapi import Request
from starlette.responses import Response
def login_description(user, response: Response):
    if response.status_code < 400:
        return f"User {getattr(user, 'email', 'Unknown')} logged in successfully"
    return f"Failed login attempt for {getattr(user, 'email', 'Unknown')}: invalid credentials"

def register_description(user, response: Response):
    return f"User {getattr(user, 'email', 'Unknown')} registered"

def view_audit_logs_description(user, response: Response):
    return f"User {getattr(user, 'username', 'Unknown')} viewed audit logs"


def generic_description(user, request: Request, response: Response):
    if user:
        return f"User {user.email} performed {request.method} on {request.url.path}"
    return f"Anonymous performed {request.method} on {request.url.path}"

# ---- mapping ----
AUDIT_DESCRIPTIONS = {
    ("POST", "/auth/login"): login_description,
    ("POST", "/auth/register"): register_description,
    ("GET", "/api/audit/logs/"): view_audit_logs_description,
}
