-- HORIZON OEE WEB - CAMADA DE SEGURANÇA
-- Execute este arquivo no SQLite principal do Horizon.
-- Seguro para rodar mais de uma vez: usa IF NOT EXISTS onde possível.

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS security_users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'OPERADOR',
    is_active INTEGER NOT NULL DEFAULT 1,
    failed_login_count INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    last_login_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT,
    updated_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_security_users_username ON security_users(username);
CREATE INDEX IF NOT EXISTS idx_security_users_email ON security_users(email);
CREATE INDEX IF NOT EXISTS idx_security_users_role ON security_users(role);
CREATE INDEX IF NOT EXISTS idx_security_users_active ON security_users(is_active);

CREATE TABLE IF NOT EXISTS security_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    permission TEXT NOT NULL,
    allowed INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(role, permission)
);

CREATE INDEX IF NOT EXISTS idx_security_permissions_role ON security_permissions(role);

CREATE TABLE IF NOT EXISTS security_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    revoked_at TEXT,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY(user_id) REFERENCES security_users(id)
);

CREATE INDEX IF NOT EXISTS idx_security_sessions_token_hash ON security_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_security_sessions_user_id ON security_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_security_sessions_expires ON security_sessions(expires_at);

CREATE TABLE IF NOT EXISTS security_audit_logs (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    user_id TEXT,
    username_snapshot TEXT,
    role_snapshot TEXT,
    action TEXT NOT NULL,
    entity TEXT,
    entity_id TEXT,
    status TEXT NOT NULL, -- success, denied, error, warning
    reason TEXT,
    before_json TEXT,
    after_json TEXT,
    ip_address TEXT,
    user_agent TEXT,
    details_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_security_audit_created_at ON security_audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_security_audit_user_id ON security_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_security_audit_action ON security_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_security_audit_entity ON security_audit_logs(entity, entity_id);
CREATE INDEX IF NOT EXISTS idx_security_audit_status ON security_audit_logs(status);

CREATE TABLE IF NOT EXISTS security_record_history (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    user_id TEXT,
    username_snapshot TEXT,
    role_snapshot TEXT,
    entity TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    before_json TEXT,
    after_json TEXT,
    reason TEXT,
    ip_address TEXT,
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_security_history_entity ON security_record_history(entity, entity_id);
CREATE INDEX IF NOT EXISTS idx_security_history_created ON security_record_history(created_at);

CREATE TABLE IF NOT EXISTS security_backups (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    created_by TEXT,
    file_path TEXT NOT NULL,
    sha256 TEXT,
    size_bytes INTEGER,
    status TEXT NOT NULL, -- success, error
    reason TEXT,
    details_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_security_backups_created ON security_backups(created_at);

CREATE TABLE IF NOT EXISTS security_integrity_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT
);

CREATE TABLE IF NOT EXISTS security_protected_mode (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    is_active INTEGER NOT NULL DEFAULT 0,
    reason TEXT,
    activated_at TEXT,
    activated_by TEXT,
    deactivated_at TEXT,
    deactivated_by TEXT
);

INSERT OR IGNORE INTO security_protected_mode (id, is_active) VALUES (1, 0);

CREATE TABLE IF NOT EXISTS security_reauth_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    action TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY(user_id) REFERENCES security_users(id)
);

CREATE INDEX IF NOT EXISTS idx_security_reauth_token_hash ON security_reauth_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_security_reauth_user ON security_reauth_tokens(user_id);

-- Caso sua tabela principal se chame registros, estes campos habilitam lixeira/soft delete.
-- Se o Horizon usar outro nome de tabela, adapte este bloco.
-- SQLite antigo não aceita ADD COLUMN IF NOT EXISTS; por isso o script Python init_security faz isso com segurança.
