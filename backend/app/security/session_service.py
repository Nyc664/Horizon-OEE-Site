import hashlib
import secrets
import uuid
from datetime import timedelta
from .config import SESSION_TTL_MINUTES, IDLE_TIMEOUT_MINUTES, REAUTH_TTL_MINUTES
from .database import get_conn, row_to_dict
from .time_utils import now_utc, now_iso, parse_iso


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user_id: str, *, ip_address: str | None = None, user_agent: str | None = None) -> str:
    token = secrets.token_urlsafe(48)
    session_id = str(uuid.uuid4())
    created = now_utc()
    expires = created + timedelta(minutes=SESSION_TTL_MINUTES)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO security_sessions (
                id, user_id, token_hash, created_at, expires_at, last_seen_at,
                ip_address, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                hash_token(token),
                created.replace(microsecond=0).isoformat(),
                expires.replace(microsecond=0).isoformat(),
                created.replace(microsecond=0).isoformat(),
                ip_address,
                user_agent,
            ),
        )
        conn.commit()
    return token


def validate_session(token: str) -> dict | None:
    if not token:
        return None
    now = now_utc()
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT s.*, u.username, u.email, u.display_name, u.role, u.is_active
            FROM security_sessions s
            JOIN security_users u ON u.id = s.user_id
            WHERE s.token_hash=? AND s.revoked_at IS NULL
            """,
            (hash_token(token),),
        ).fetchone()
        if not row:
            return None
        session = row_to_dict(row)
        if not session.get("is_active"):
            return None
        expires_at = parse_iso(session.get("expires_at"))
        last_seen_at = parse_iso(session.get("last_seen_at"))
        if expires_at and now > expires_at:
            conn.execute("UPDATE security_sessions SET revoked_at=? WHERE id=?", (now_iso(), session["id"]))
            conn.commit()
            return None
        if last_seen_at and now - last_seen_at > timedelta(minutes=IDLE_TIMEOUT_MINUTES):
            conn.execute("UPDATE security_sessions SET revoked_at=? WHERE id=?", (now_iso(), session["id"]))
            conn.commit()
            return None
        conn.execute("UPDATE security_sessions SET last_seen_at=? WHERE id=?", (now_iso(), session["id"]))
        conn.commit()
        return {
            "id": session["user_id"],
            "session_id": session["id"],
            "username": session["username"],
            "email": session["email"],
            "display_name": session["display_name"],
            "role": session["role"],
            "is_active": bool(session["is_active"]),
        }


def revoke_session(token: str) -> bool:
    if not token:
        return False
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE security_sessions SET revoked_at=? WHERE token_hash=? AND revoked_at IS NULL",
            (now_iso(), hash_token(token)),
        )
        conn.commit()
        return cur.rowcount > 0


def revoke_all_user_sessions(user_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE security_sessions SET revoked_at=? WHERE user_id=? AND revoked_at IS NULL",
            (now_iso(), user_id),
        )
        conn.commit()


def create_reauth_token(user_id: str, action: str, *, ip_address=None, user_agent=None) -> str:
    token = secrets.token_urlsafe(32)
    created = now_utc()
    expires = created + timedelta(minutes=REAUTH_TTL_MINUTES)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO security_reauth_tokens
            (id, user_id, token_hash, action, created_at, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), user_id, hash_token(token), action, created.replace(microsecond=0).isoformat(), expires.replace(microsecond=0).isoformat(), ip_address, user_agent),
        )
        conn.commit()
    return token


def consume_reauth_token(user_id: str, action: str, token: str) -> bool:
    if not token:
        return False
    now = now_utc()
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM security_reauth_tokens
            WHERE user_id=? AND action=? AND token_hash=? AND used_at IS NULL
            """,
            (user_id, action, hash_token(token)),
        ).fetchone()
        if not row:
            return False
        expires = parse_iso(row["expires_at"])
        if expires and now > expires:
            return False
        conn.execute("UPDATE security_reauth_tokens SET used_at=? WHERE id=?", (now_iso(), row["id"]))
        conn.commit()
        return True
