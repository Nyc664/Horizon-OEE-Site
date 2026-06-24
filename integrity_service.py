import hashlib
import json
from .config import INTEGRITY_TABLES
from .database import get_conn, table_exists
from .time_utils import now_iso
from .audit_service import audit_log
from .protected_mode import activate_protected_mode


def pragma_integrity_check() -> tuple[bool, str]:
    with get_conn() as conn:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    msg = row[0] if row else "sem retorno"
    return msg == "ok", msg


def compute_table_checksum(table_name: str) -> str | None:
    with get_conn() as conn:
        if not table_exists(conn, table_name):
            return None
        cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]
        if not cols:
            return None
        # Ordenação genérica. Se existir id, usa id; senão usa rowid.
        order_col = "id" if "id" in cols else "rowid"
        rows = conn.execute(f"SELECT * FROM {table_name} ORDER BY {order_col}").fetchall()
    h = hashlib.sha256()
    for row in rows:
        data = {k: row[k] for k in row.keys()}
        h.update(json.dumps(data, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8"))
    return h.hexdigest()


def current_integrity_snapshot() -> dict:
    snapshot = {}
    for table in INTEGRITY_TABLES:
        checksum = compute_table_checksum(table)
        if checksum is not None:
            snapshot[f"table:{table}"] = checksum
    return snapshot


def mark_integrity_known_good(*, user: dict | None = None, reason: str = "known_good") -> dict:
    snapshot = current_integrity_snapshot()
    with get_conn() as conn:
        for key, value in snapshot.items():
            conn.execute(
                """
                INSERT INTO security_integrity_state (key, value, updated_at, updated_by)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at, updated_by=excluded.updated_by
                """,
                (key, value, now_iso(), user.get("id") if user else None),
            )
        conn.commit()
    audit_log(action="integridade_marcada_como_valida", status="success", user=user, reason=reason, details={"tables": list(snapshot.keys())})
    return snapshot


def verify_integrity(*, user: dict | None = None, activate_protected_on_fail: bool = True) -> dict:
    ok_db, msg = pragma_integrity_check()
    snapshot = current_integrity_snapshot()
    divergences = []
    with get_conn() as conn:
        for key, current in snapshot.items():
            row = conn.execute("SELECT value FROM security_integrity_state WHERE key=?", (key,)).fetchone()
            if row and row["value"] != current:
                divergences.append({"key": key, "expected": row["value"], "current": current})
    result = {"sqlite_ok": ok_db, "sqlite_message": msg, "divergences": divergences, "ok": ok_db and not divergences}
    if result["ok"]:
        audit_log(action="integridade_verificada", status="success", user=user, details=result)
    else:
        audit_log(action="integridade_falhou", status="warning", user=user, details=result)
        if activate_protected_on_fail:
            activate_protected_mode("Falha ou divergência de integridade detectada.", user=user)
    return result
