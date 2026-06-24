import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .config import DB_PATH, BACKUP_DIR, BACKUP_RETENTION_DAYS
from .database import get_conn
from .time_utils import now_iso
from .audit_service import audit_log


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def create_backup(*, reason: str = "manual", user: dict | None = None) -> dict:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"horizon_backup_{ts_name}.sqlite"
    backup_id = str(uuid.uuid4())
    try:
        source = sqlite3.connect(DB_PATH)
        dest = sqlite3.connect(backup_path)
        with dest:
            source.backup(dest)
        source.close()
        dest.close()
        digest = sha256_file(backup_path)
        size = backup_path.stat().st_size
        status = "success"
        details = {"db_path": str(DB_PATH), "backup_path": str(backup_path)}
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO security_backups
                (id, created_at, created_by, file_path, sha256, size_bytes, status, reason, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (backup_id, now_iso(), user.get("id") if user else None, str(backup_path), digest, size, status, reason, json.dumps(details, ensure_ascii=False)),
            )
            conn.commit()
        audit_log(action="backup_criado", status="success", user=user, entity="backup", entity_id=backup_id, reason=reason, details=details)
        return {"id": backup_id, "path": str(backup_path), "sha256": digest, "size_bytes": size, "status": status}
    except Exception as exc:
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO security_backups
                (id, created_at, created_by, file_path, status, reason, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (backup_id, now_iso(), user.get("id") if user else None, str(backup_path), "error", reason, json.dumps({"error": str(exc)}, ensure_ascii=False)),
            )
            conn.commit()
        audit_log(action="backup_falhou", status="error", user=user, entity="backup", entity_id=backup_id, reason=reason, details={"error": str(exc)})
        raise


def cleanup_old_backups(retention_days: int = BACKUP_RETENTION_DAYS) -> list[str]:
    removed = []
    if not BACKUP_DIR.exists():
        return removed
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    for path in BACKUP_DIR.glob("horizon_backup_*.sqlite"):
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff:
            try:
                path.unlink()
                removed.append(str(path))
            except OSError:
                pass
    return removed
