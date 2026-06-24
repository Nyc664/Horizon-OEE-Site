import uuid
from datetime import timedelta
from .config import MAX_LOGIN_FAILURES, LOCKOUT_MINUTES
from .database import get_conn, row_to_dict
from .password_service import hash_password, verify_password, needs_rehash
from .time_utils import now_utc, now_iso, parse_iso

VALID_ROLES = {"OPERADOR", "ADMIN", "ADMIN_MASTER"}


def get_user_by_login(login: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM security_users
            WHERE lower(username)=lower(?) OR lower(email)=lower(?)
            LIMIT 1
            """,
            (login, login),
        ).fetchone()
    return row_to_dict(row)


def get_user_by_id(user_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM security_users WHERE id=?", (user_id,)).fetchone()
    return row_to_dict(row)


def create_user(*, username: str, display_name: str, password: str, role: str = "OPERADOR", email: str | None = None, created_by: str | None = None) -> dict:
    if role not in VALID_ROLES:
        raise ValueError("Perfil inválido.")
    user_id = str(uuid.uuid4())
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO security_users
            (id, username, email, display_name, password_hash, role, is_active, created_at, updated_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (user_id, username.strip(), email.strip() if email else None, display_name.strip(), hash_password(password), role, ts, ts, created_by),
        )
        conn.commit()
    return get_user_by_id(user_id)


def is_user_locked(user: dict) -> bool:
    locked_until = parse_iso(user.get("locked_until"))
    return bool(locked_until and now_utc() < locked_until)


def register_login_failure(user: dict | None) -> None:
    if not user:
        return
    new_count = int(user.get("failed_login_count") or 0) + 1
    locked_until = None
    if new_count >= MAX_LOGIN_FAILURES:
        locked_until = (now_utc() + timedelta(minutes=LOCKOUT_MINUTES)).replace(microsecond=0).isoformat()
    with get_conn() as conn:
        conn.execute(
            "UPDATE security_users SET failed_login_count=?, locked_until=?, updated_at=? WHERE id=?",
            (new_count, locked_until, now_iso(), user["id"]),
        )
        conn.commit()


def register_login_success(user: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE security_users
            SET failed_login_count=0, locked_until=NULL, last_login_at=?, updated_at=?
            WHERE id=?
            """,
            (now_iso(), now_iso(), user["id"]),
        )
        conn.commit()


def authenticate(login: str, password: str) -> tuple[bool, dict | None, str]:
    user = get_user_by_login(login)
    if not user:
        return False, None, "invalid"
    if not user.get("is_active"):
        return False, user, "inactive"
    if is_user_locked(user):
        return False, user, "locked"
    if not verify_password(password, user.get("password_hash", "")):
        register_login_failure(user)
        return False, user, "invalid"
    if needs_rehash(user.get("password_hash", "")):
        with get_conn() as conn:
            conn.execute("UPDATE security_users SET password_hash=?, updated_at=? WHERE id=?", (hash_password(password), now_iso(), user["id"]))
            conn.commit()
    register_login_success(user)
    return True, get_user_by_id(user["id"]), "ok"


def update_password(user_id: str, new_password: str, updated_by: str | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE security_users SET password_hash=?, updated_at=?, updated_by=? WHERE id=?",
            (hash_password(new_password), now_iso(), updated_by, user_id),
        )
        conn.commit()


def set_user_role(user_id: str, role: str, updated_by: str | None = None) -> dict:
    if role not in VALID_ROLES:
        raise ValueError("Perfil inválido.")
    with get_conn() as conn:
        conn.execute("UPDATE security_users SET role=?, updated_at=?, updated_by=? WHERE id=?", (role, now_iso(), updated_by, user_id))
        conn.commit()
    return get_user_by_id(user_id)


def set_user_active(user_id: str, is_active: bool, updated_by: str | None = None) -> dict:
    with get_conn() as conn:
        conn.execute("UPDATE security_users SET is_active=?, updated_at=?, updated_by=? WHERE id=?", (1 if is_active else 0, now_iso(), updated_by, user_id))
        conn.commit()
    return get_user_by_id(user_id)
