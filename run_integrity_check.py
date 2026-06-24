import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.security.integrity_service import verify_integrity

if __name__ == "__main__":
    print(verify_integrity(activate_protected_on_fail=True))
