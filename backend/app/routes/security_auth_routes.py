from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Request, Depends
from app.security.user_service import authenticate, verify_password, get_user_by_id
from app.security.session_service import create_session, revoke_session, create_reauth_token
from app.security.auth_dependencies import get_current_user
from app.security.audit_service import audit_log
from app.security.permissions import user_has_permission

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    login: str = Field(..., min_length=2)
    password: str = Field(..., min_length=1)

class ReauthRequest(BaseModel):
    password: str
    action: str


def _client_info(request: Request):
    return getattr(request.client, "host", None), request.headers.get("user-agent")

@router.post("/login")
def login(payload: LoginRequest, request: Request):
    ip, ua = _client_info(request)
    ok, user, status = authenticate(payload.login, payload.password)
    # Mensagem genérica para não revelar se usuário existe.
    if not ok:
        audit_log(
            action="login_falhou",
            status="denied",
            user=user,
            reason=status,
            ip_address=ip,
            user_agent=ua,
            details={"login": payload.login},
        )
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")
    token = create_session(user["id"], ip_address=ip, user_agent=ua)
    audit_log(action="login_sucesso", status="success", user=user, ip_address=ip, user_agent=ua)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "role": user["role"],
        },
    }

@router.post("/logout")
def logout(request: Request, user: dict = Depends(get_current_user)):
    ip, ua = _client_info(request)
    auth = request.headers.get("authorization", "")
    token = auth.replace("Bearer ", "", 1).strip() if auth.lower().startswith("bearer ") else request.cookies.get("horizon_session")
    revoke_session(token)
    audit_log(action="logout", status="success", user=user, ip_address=ip, user_agent=ua)
    return {"ok": True}

@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    # Permissões booleanas úteis para o frontend esconder/mostrar botões. Não substituem validação do backend.
    perms = [
        "registros.visualizar", "registros.criar", "registros.editar", "registros.soft_delete",
        "registros.restaurar", "registros.delete_definitivo", "usuarios.visualizar", "auditoria.visualizar",
        "backup.criar", "backup.restaurar", "exportar.csv", "exportar.excel", "exportar.pdf", "dashboard.visualizar"
    ]
    return {"user": user, "permissions": {p: user_has_permission(user, p) for p in perms}}

@router.post("/reauth")
def reauth(payload: ReauthRequest, request: Request, user: dict = Depends(get_current_user)):
    ip, ua = _client_info(request)
    full_user = get_user_by_id(user["id"])
    if not full_user or not verify_password(payload.password, full_user["password_hash"]):
        audit_log(action="reauth_falhou", status="denied", user=user, reason=payload.action, ip_address=ip, user_agent=ua)
        raise HTTPException(status_code=401, detail="Senha inválida.")
    token = create_reauth_token(user["id"], payload.action, ip_address=ip, user_agent=ua)
    audit_log(action="reauth_sucesso", status="success", user=user, reason=payload.action, ip_address=ip, user_agent=ua)
    return {"reauth_token": token, "action": payload.action}
