"""
Inicializa a camada de segurança no SQLite do Horizon.
Uso:
  python scripts/init_security.py

Variáveis úteis:
  HORIZON_DB_PATH=data/horizon.sqlite
"""
import sys
from pathlib import Path

# Permite rodar pelo diretório raiz do projeto.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.security.database import get_conn, add_column_if_missing, table_exists
from app.security.permissions import seed_default_permissions
from app.security.integrity_service import mark_integrity_known_good, pragma_integrity_check
from app.security.backup_service import create_backup
from app.security.config import DB_PATH

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "migrations" / "001_security_schema.sql"


def apply_schema():
    with get_conn() as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        # Se existir tabela registros, adiciona campos de lixeira com segurança.
        if table_exists(conn, "registros"):
            for col in [
                "deleted_at TEXT",
                "deleted_by TEXT",
                "delete_reason TEXT",
                "restored_at TEXT",
                "restored_by TEXT",
                "restore_reason TEXT",
                "permanently_deleted_at TEXT",
                "permanently_deleted_by TEXT",
                "permanent_delete_reason TEXT",
            ]:
                add_column_if_missing(conn, "registros", col)
        conn.commit()


def main():
    print(f"Banco alvo: {DB_PATH}")
    apply_schema()
    print("Schema de segurança aplicado.")
    seed_default_permissions()
    print("Permissões padrão criadas/atualizadas.")
    ok, msg = pragma_integrity_check()
    print(f"PRAGMA integrity_check: {msg}")
    create_backup(reason="backup inicial após init_security")
    print("Backup inicial criado.")
    mark_integrity_known_good(reason="estado inicial após init_security")
    print("Hash de integridade inicial salvo.")
    print("OK. Agora crie o Admin Master com: python scripts/create_admin_master.py")

if __name__ == "__main__":
    main()
