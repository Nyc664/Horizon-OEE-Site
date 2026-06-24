"""
EXEMPLO de como proteger rotas de registros.
Adapte ao nome real da tabela/rotas do Horizon.

A regra é: todo endpoint crítico chama require_permission(), assert_not_protected(),
auditoria e histórico antes/depois.
"""
import json
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request
from app.security.auth_dependencies import require_permission
from app.security.database import get_conn, row_to_dict, table_exists
from app.security.audit_service import audit_log, record_history
from app.security.time_utils import now_iso
from app.security.session_service import consume_reauth_token
from app.security.integrity_service import mark_integrity_known_good

router = APIRouter(prefix="/api/registros", tags=["registros-security-example"])

class EditRegistroRequest(BaseModel):
    campos: dict
    motivo: str | None = None

class DeleteRegistroRequest(BaseModel):
    motivo: str = Field(..., min_length=3)
    reauth_token: str | None = None

class RestoreRegistroRequest(BaseModel):
    motivo: str = Field(..., min_length=3)
    reauth_token: str | None = None


def _client_info(request: Request):
    return getattr(request.client, "host", None), request.headers.get("user-agent")


def _get_registro(conn, registro_id: str):
    if not table_exists(conn, "registros"):
        raise HTTPException(status_code=500, detail="Tabela registros não encontrada. Adapte a rota ao nome real da tabela.")
    row = conn.execute("SELECT * FROM registros WHERE id=?", (registro_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")
    return row_to_dict(row)

@router.put("/{registro_id}")
def editar_registro(registro_id: str, payload: EditRegistroRequest, request: Request, user: dict = Depends(require_permission("registros.editar", block_in_protected_mode=True))):
    ip, ua = _client_info(request)
    campos_permitidos = {"linha", "motivo", "observacao", "status", "hora_fim", "quantidade", "turno"}
    updates = {k: v for k, v in payload.campos.items() if k in campos_permitidos}
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo permitido informado.")
    with get_conn() as conn:
        before = _get_registro(conn, registro_id)
        set_sql = ", ".join([f"{k}=?" for k in updates.keys()])
        values = list(updates.values()) + [registro_id]
        conn.execute(f"UPDATE registros SET {set_sql} WHERE id=?", values)
        after = _get_registro(conn, registro_id)
        conn.commit()
    audit_log(action="registro_editado", status="success", user=user, entity="registros", entity_id=registro_id, reason=payload.motivo, before=before, after=after, ip_address=ip, user_agent=ua)
    record_history(user=user, entity="registros", entity_id=registro_id, action="editar", before=before, after=after, reason=payload.motivo, ip_address=ip, user_agent=ua)
    mark_integrity_known_good(user=user, reason="edição realizada pelo sistema")
    return {"ok": True, "registro": after}

@router.delete("/{registro_id}")
def soft_delete_registro(registro_id: str, payload: DeleteRegistroRequest, request: Request, user: dict = Depends(require_permission("registros.soft_delete", block_in_protected_mode=True))):
    ip, ua = _client_info(request)
    if payload.reauth_token and not consume_reauth_token(user["id"], "registros.soft_delete", payload.reauth_token):
        raise HTTPException(status_code=401, detail="Reautenticação inválida ou expirada.")
    with get_conn() as conn:
        before = _get_registro(conn, registro_id)
        conn.execute(
            """
            UPDATE registros
            SET deleted_at=?, deleted_by=?, delete_reason=?
            WHERE id=? AND deleted_at IS NULL
            """,
            (now_iso(), user["id"], payload.motivo, registro_id),
        )
        after = _get_registro(conn, registro_id)
        conn.commit()
    audit_log(action="registro_excluido_logicamente", status="success", user=user, entity="registros", entity_id=registro_id, reason=payload.motivo, before=before, after=after, ip_address=ip, user_agent=ua)
    record_history(user=user, entity="registros", entity_id=registro_id, action="soft_delete", before=before, after=after, reason=payload.motivo, ip_address=ip, user_agent=ua)
    mark_integrity_known_good(user=user, reason="soft delete pelo sistema")
    return {"ok": True}

@router.post("/{registro_id}/restore")
def restore_registro(registro_id: str, payload: RestoreRegistroRequest, request: Request, user: dict = Depends(require_permission("registros.restaurar", block_in_protected_mode=True))):
    ip, ua = _client_info(request)
    with get_conn() as conn:
        before = _get_registro(conn, registro_id)
        conn.execute(
            """
            UPDATE registros
            SET deleted_at=NULL, deleted_by=NULL, delete_reason=NULL,
                restored_at=?, restored_by=?, restore_reason=?
            WHERE id=?
            """,
            (now_iso(), user["id"], payload.motivo, registro_id),
        )
        after = _get_registro(conn, registro_id)
        conn.commit()
    audit_log(action="registro_restaurado", status="success", user=user, entity="registros", entity_id=registro_id, reason=payload.motivo, before=before, after=after, ip_address=ip, user_agent=ua)
    record_history(user=user, entity="registros", entity_id=registro_id, action="restore", before=before, after=after, reason=payload.motivo, ip_address=ip, user_agent=ua)
    mark_integrity_known_good(user=user, reason="restauração pelo sistema")
    return {"ok": True, "registro": after}

@router.delete("/{registro_id}/definitivo")
def delete_definitivo(registro_id: str, payload: DeleteRegistroRequest, request: Request, user: dict = Depends(require_permission("registros.delete_definitivo", block_in_protected_mode=True))):
    ip, ua = _client_info(request)
    if user.get("role") != "ADMIN_MASTER":
        audit_log(action="delete_definitivo_negado", status="denied", user=user, entity="registros", entity_id=registro_id, reason="Somente ADMIN_MASTER", ip_address=ip, user_agent=ua)
        raise HTTPException(status_code=403, detail="Somente Admin Master pode apagar definitivamente.")
    if payload.reauth_token and not consume_reauth_token(user["id"], "registros.delete_definitivo", payload.reauth_token):
        raise HTTPException(status_code=401, detail="Reautenticação inválida ou expirada.")
    with get_conn() as conn:
        before = _get_registro(conn, registro_id)
        conn.execute("DELETE FROM registros WHERE id=?", (registro_id,))
        conn.commit()
    audit_log(action="registro_apagado_definitivamente", status="success", user=user, entity="registros", entity_id=registro_id, reason=payload.motivo, before=before, after=None, ip_address=ip, user_agent=ua)
    record_history(user=user, entity="registros", entity_id=registro_id, action="delete_definitivo", before=before, after=None, reason=payload.motivo, ip_address=ip, user_agent=ua)
    mark_integrity_known_good(user=user, reason="delete definitivo pelo sistema")
    return {"ok": True}
