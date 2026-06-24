from pathlib import Path
import os

BASE_DIR = Path(os.getenv("HORIZON_BASE_DIR", ".")).resolve()
DB_PATH = Path(os.getenv("HORIZON_DB_PATH", str(BASE_DIR / "data" / "horizon.sqlite"))).resolve()
BACKUP_DIR = Path(os.getenv("HORIZON_BACKUP_DIR", str(BASE_DIR / "backups"))).resolve()

SESSION_TTL_MINUTES = int(os.getenv("HORIZON_SESSION_TTL_MINUTES", "480"))  # 8h total
IDLE_TIMEOUT_MINUTES = int(os.getenv("HORIZON_IDLE_TIMEOUT_MINUTES", "60"))
REAUTH_TTL_MINUTES = int(os.getenv("HORIZON_REAUTH_TTL_MINUTES", "5"))
MAX_LOGIN_FAILURES = int(os.getenv("HORIZON_MAX_LOGIN_FAILURES", "5"))
LOCKOUT_MINUTES = int(os.getenv("HORIZON_LOCKOUT_MINUTES", "15"))
BACKUP_RETENTION_DAYS = int(os.getenv("HORIZON_BACKUP_RETENTION_DAYS", "30"))

# Produção: deixa barreiras visuais no frontend. Nunca confiar nisso como segurança real.
ENABLE_FRONTEND_DEVTOOLS_BARRIER = os.getenv("HORIZON_ENABLE_DEVTOOLS_BARRIER", "1") == "1"

# Tabelas críticas usadas para checksum simples contra alteração manual.
# Ajuste conforme o nome real das tabelas do Horizon.
INTEGRITY_TABLES = [
    t.strip() for t in os.getenv(
        "HORIZON_INTEGRITY_TABLES",
        "security_users,security_permissions,registros,apontamentos,oee_registros"
    ).split(",") if t.strip()
]

CRITICAL_ACTIONS = {
    "registros.soft_delete",
    "registros.delete_definitivo",
    "registros.restaurar",
    "usuarios.criar",
    "usuarios.editar",
    "usuarios.desativar",
    "usuarios.permissoes",
    "backup.restaurar",
    "lixeira.limpar",
}
