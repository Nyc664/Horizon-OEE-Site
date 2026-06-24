from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from app.security.auth_dependencies import require_permission, get_current_user
from app.security.database import get_conn, row_to_dict
from app.security.user_service import create_user, set_user_active, set_user_role, get_user_by_id
from app.security.permissions import seed_default_permissions
from app.security.audit_service import audit_log
from app.security.backup_service import create_backup, cleanup_old_backups
from app.security.integrity_service import verify_integrity, mark_integrity_known_good
from app.security.protected_mode import get_protected_mode, deactivate_protected_mode, activate_protected_mode

router = APIRouter(prefix="/api/security", tags=["security"])

class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=2)
    display_name: str = Field(..., min_length=2)
    password: str = Field(..., min_length=8)
    role: str = "OPERADOR"
    email: str | None = None

class RoleRequest(BaseModel):
    role: str

class ReasonRequest(BaseModel):
    reason: str = Field(..., min_length=3)


def _client_info(request: Request):
    return getattr(request.client, "host", None), request.headers.get("user-agent")

@router.get("/audit")
def list_audit(
    limit: int = Query(default=100, le=500),
    user: dict = Depends(require_permission("auditoria.visualizar")),
):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM security_audit_logs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return {"items": [row_to_dict(r) for r in rows]}

@router.get("/users")
def list_users(user: dict = Depends(require_permission("usuarios.visualizar"))):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, username, email, display_name, role, is_active, failed_login_count, locked_until, last_login_at, created_at FROM security_users ORDER BY display_name"
        ).fetchall()
    return {"items": [row_to_dict(r) for r in rows]}

@router.post("/users")
def api_create_user(payload: CreateUserRequest, request: Request, user: dict = Depends(require_permission("usuarios.criar", block_in_protected_mode=True))):
    ip, ua = _client_info(request)
    new_user = create_user(username=payload.username, display_name=payload.display_name, password=payload.password, role=payload.role, email=payload.email, created_by=user["id"])
    audit_log(action="usuario_criado", status="success", user=user, entity="security_users", entity_id=new_user["id"], after={k: v for k, v in new_user.items() if k != "password_hash"}, ip_address=ip, user_agent=ua)
    return {"user": {k: v for k, v in new_user.items() if k != "password_hash"}}

@router.patch("/users/{user_id}/role")
def api_set_role(user_id: str, payload: RoleRequest, request: Request, user: dict = Depends(require_permission("usuarios.permissoes", block_in_protected_mode=True))):
    ip, ua = _client_info(request)
    before = get_user_by_id(user_id)
    if not before:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    after = set_user_role(user_id, payload.role, updated_by=user["id"])
    audit_log(action="usuario_perfil_alterado", status="success", user=user, entity="security_users", entity_id=user_id, before={k:v for k,v in before.items() if k != "password_hash"}, after={k:v for k,v in after.items() if k != "password_hash"}, ip_address=ip, user_agent=ua)
    return {"user": {k:v for k,v in after.items() if k != "password_hash"}}

@router.patch("/users/{user_id}/disable")
def api_disable_user(user_id: str, payload: ReasonRequest, request: Request, user: dict = Depends(require_permission("usuarios.desativar", block_in_protected_mode=True))):
    ip, ua = _client_info(request)
    before = get_user_by_id(user_id)
    if not before:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    after = set_user_active(user_id, False, updated_by=user["id"])
    audit_log(action="usuario_desativado", status="success", user=user, entity="security_users", entity_id=user_id, reason=payload.reason, before={k:v for k,v in before.items() if k != "password_hash"}, after={k:v for k,v in after.items() if k != "password_hash"}, ip_address=ip, user_agent=ua)
    return {"ok": True}

@router.post("/backup")
def api_backup(payload: ReasonRequest, user: dict = Depends(require_permission("backup.criar", block_in_protected_mode=False))):
    backup = create_backup(reason=payload.reason, user=user)
    cleanup_old_backups()
    return backup

@router.post("/integrity/check")
def api_integrity_check(user: dict = Depends(require_permission("sistema.integridade"))):
    return verify_integrity(user=user, activate_protected_on_fail=True)

@router.post("/integrity/known-good")
def api_integrity_known_good(payload: ReasonRequest, user: dict = Depends(require_permission("sistema.integridade"))):
    return mark_integrity_known_good(user=user, reason=payload.reason)

@router.get("/protected-mode")
def api_protected_mode(user: dict = Depends(get_current_user)):
    return get_protected_mode()

@router.post("/protected-mode/activate")
def api_activate_protected(payload: ReasonRequest, user: dict = Depends(require_permission("sistema.modo_protegido"))):
    activate_protected_mode(payload.reason, user=user)
    return get_protected_mode()

@router.post("/protected-mode/deactivate")
def api_deactivate_protected(payload: ReasonRequest, user: dict = Depends(require_permission("sistema.modo_protegido"))):
    if user.get("role") != "ADMIN_MASTER":
        raise HTTPException(status_code=403, detail="Somente Admin Master pode desativar modo protegido.")
    deactivate_protected_mode(payload.reason, user=user)
    return get_protected_mode()

@router.post("/permissions/seed")
def api_seed_permissions(user: dict = Depends(require_permission("usuarios.permissoes"))):
    seed_default_permissions()
    audit_log(action="permissoes_padrao_recriadas", status="success", user=user)
    return {"ok": True}
