from .database import get_conn, row_to_dict
from .time_utils import now_iso
from .audit_service import audit_log


def get_protected_mode() -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM security_protected_mode WHERE id=1").fetchone()
        if row is None:
            conn.execute("INSERT INTO security_protected_mode (id, is_active) VALUES (1, 0)")
            conn.commit()
            row = conn.execute("SELECT * FROM security_protected_mode WHERE id=1").fetchone()
    data = row_to_dict(row)
    data["is_active"] = bool(data.get("is_active"))
    return data


def is_protected_mode_active() -> bool:
    return bool(get_protected_mode().get("is_active"))


def activate_protected_mode(reason: str, *, user: dict | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE security_protected_mode
            SET is_active=1, reason=?, activated_at=?, activated_by=?
            WHERE id=1
            """,
            (reason, now_iso(), user.get("id") if user else None),
        )
        conn.commit()
    audit_log(action="modo_protegido_ativado", status="warning", user=user, reason=reason)


def deactivate_protected_mode(reason: str, *, user: dict | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE security_protected_mode
            SET is_active=0, reason=?, deactivated_at=?, deactivated_by=?
            WHERE id=1
            """,
            (reason, now_iso(), user.get("id") if user else None),
        )
        conn.commit()
    audit_log(action="modo_protegido_desativado", status="success", user=user, reason=reason)


def assert_not_protected(user: dict | None = None):
    if is_protected_mode_active() and (not user or user.get("role") != "ADMIN_MASTER"):
        try:
            from fastapi import HTTPException
            raise HTTPException(status_code=423, detail="Sistema em modo protegido. Ação bloqueada.")
        except ImportError:
            raise RuntimeError("Sistema em modo protegido. Ação bloqueada.")
