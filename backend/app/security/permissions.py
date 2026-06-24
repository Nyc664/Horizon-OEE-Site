from .database import get_conn
from .time_utils import now_iso
from .audit_service import audit_log

PERMISSIONS = [
    "registros.visualizar",
    "registros.criar",
    "registros.editar",
    "registros.soft_delete",
    "registros.restaurar",
    "registros.delete_definitivo",
    "usuarios.visualizar",
    "usuarios.criar",
    "usuarios.editar",
    "usuarios.desativar",
    "usuarios.permissoes",
    "backup.criar",
    "backup.restaurar",
    "auditoria.visualizar",
    "exportar.csv",
    "exportar.excel",
    "exportar.pdf",
    "dashboard.visualizar",
    "sistema.integridade",
    "sistema.modo_protegido",
]

DEFAULT_ROLE_PERMISSIONS = {
    "OPERADOR": {
        "registros.visualizar",
        "registros.criar",
        "dashboard.visualizar",
    },
    "ADMIN": {
        "registros.visualizar",
        "registros.criar",
        "registros.editar",
        "registros.soft_delete",
        "registros.restaurar",
        "backup.criar",
        "exportar.csv",
        "exportar.excel",
        "exportar.pdf",
        "dashboard.visualizar",
    },
    "ADMIN_MASTER": set(PERMISSIONS),
}


def seed_default_permissions() -> None:
    with get_conn() as conn:
        for role, allowed_perms in DEFAULT_ROLE_PERMISSIONS.items():
            for permission in PERMISSIONS:
                conn.execute(
                    """
                    INSERT INTO security_permissions (role, permission, allowed, created_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(role, permission) DO UPDATE SET allowed=excluded.allowed
                    """,
                    (role, permission, 1 if permission in allowed_perms else 0, now_iso()),
                )
        conn.commit()


def user_has_permission(user: dict, permission: str) -> bool:
    if not user or not user.get("is_active"):
        return False
    role = user.get("role")
    if role == "ADMIN_MASTER":
        return True
    with get_conn() as conn:
        row = conn.execute(
            "SELECT allowed FROM security_permissions WHERE role=? AND permission=?",
            (role, permission),
        ).fetchone()
    return bool(row and row["allowed"] == 1)


def assert_permission(user: dict, permission: str, *, request=None, entity=None, entity_id=None) -> None:
    if user_has_permission(user, permission):
        return
    ip = getattr(getattr(request, "client", None), "host", None) if request else None
    ua = request.headers.get("user-agent") if request else None
    audit_log(
        action="tentativa_sem_permissao",
        status="denied",
        user=user,
        entity=entity,
        entity_id=entity_id,
        reason=f"Permissao exigida: {permission}",
        ip_address=ip,
        user_agent=ua,
        details={"permission": permission},
    )
    try:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Sem permissão para esta ação.")
    except ImportError:
        raise PermissionError("Sem permissão para esta ação.")
