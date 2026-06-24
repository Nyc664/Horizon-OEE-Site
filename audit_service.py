import json
import uuid
from typing import Any
from .database import get_conn
from .time_utils import now_iso


def _json(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        return json.dumps({"erro": "valor nao serializavel"}, ensure_ascii=False)


def audit_log(
    *,
    action: str,
    status: str = "success",
    user: dict | None = None,
    entity: str | None = None,
    entity_id: str | None = None,
    reason: str | None = None,
    before: Any = None,
    after: Any = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: Any = None,
) -> str:
    log_id = str(uuid.uuid4())
    user = user or {}
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO security_audit_logs (
                id, created_at, user_id, username_snapshot, role_snapshot,
                action, entity, entity_id, status, reason,
                before_json, after_json, ip_address, user_agent, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                now_iso(),
                user.get("id"),
                user.get("username"),
                user.get("role"),
                action,
                entity,
                str(entity_id) if entity_id is not None else None,
                status,
                reason,
                _json(before),
                _json(after),
                ip_address,
                user_agent,
                _json(details),
            ),
        )
        conn.commit()
    return log_id


def record_history(
    *,
    user: dict | None,
    entity: str,
    entity_id: str,
    action: str,
    before: Any = None,
    after: Any = None,
    reason: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> str:
    history_id = str(uuid.uuid4())
    user = user or {}
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO security_record_history (
                id, created_at, user_id, username_snapshot, role_snapshot,
                entity, entity_id, action, before_json, after_json, reason, ip_address, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                history_id,
                now_iso(),
                user.get("id"),
                user.get("username"),
                user.get("role"),
                entity,
                str(entity_id),
                action,
                _json(before),
                _json(after),
                reason,
                ip_address,
                user_agent,
            ),
        )
        conn.commit()
    return history_id
