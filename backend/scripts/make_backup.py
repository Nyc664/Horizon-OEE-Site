import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.security.backup_service import create_backup, cleanup_old_backups

if __name__ == "__main__":
    result = create_backup(reason="backup manual via script")
    cleanup_old_backups()
    print(result)
