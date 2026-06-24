from typing import Callable
try:
    from fastapi import Depends, Header, HTTPException, Request
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
except Exception:  # permite importar em scripts sem FastAPI instalado
    Depends = Header = HTTPException = Request = None
    HTTPBearer = HTTPAuthorizationCredentials = None

from .session_service import validate_session
from .permissions import assert_permission
from .protected_mode import assert_not_protected

if HTTPBearer:
    bearer_scheme = HTTPBearer(auto_error=False)
else:
    bearer_scheme = None


def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    token = None
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
    if not token:
        token = request.cookies.get("horizon_session") if request else None
    user = validate_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")
    return user


def require_permission(permission: str, *, block_in_protected_mode: bool = False) -> Callable:
    def dependency(request: Request, user: dict = Depends(get_current_user)) -> dict:
        if block_in_protected_mode:
            assert_not_protected(user)
        assert_permission(user, permission, request=request)
        return user
    return dependency
