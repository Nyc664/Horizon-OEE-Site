from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
ROOT_DIR = BACKEND_DIR.parent
WEB_SECURITY_DIR = ROOT_DIR / "web" / "security"
INDEX_FILE = ROOT_DIR / "index.html"

app = FastAPI(title="Horizon OEE Seguro", version="1.0.0")

try:
    from app.routes.security_auth_routes import router as security_auth_router
    app.include_router(security_auth_router)
except Exception as exc:
    print(f"[HORIZON][AVISO] security_auth_routes nao carregou: {exc}")

try:
    from app.routes.security_admin_routes import router as security_admin_router
    app.include_router(security_admin_router)
except Exception as exc:
    print(f"[HORIZON][AVISO] security_admin_routes nao carregou: {exc}")

try:
    from app.routes.security_registros_example_routes import router as security_registros_router
    app.include_router(security_registros_router)
except Exception as exc:
    print(f"[HORIZON][AVISO] security_registros_example_routes nao carregou: {exc}")

if WEB_SECURITY_DIR.exists():
    app.mount("/security", StaticFiles(directory=str(WEB_SECURITY_DIR)), name="security")

@app.get("/")
def home():
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    return JSONResponse(
        {"ok": False, "erro": "index.html nao encontrado", "esperado": str(INDEX_FILE)},
        status_code=404,
    )

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "Horizon OEE Seguro",
        "backend_dir": str(BACKEND_DIR),
        "root_dir": str(ROOT_DIR),
        "index_exists": INDEX_FILE.exists(),
        "security_static_exists": WEB_SECURITY_DIR.exists(),
    }

@app.on_event("startup")
def startup_security():
    try:
        from app.security.backup_service import create_backup, cleanup_old_backups
        create_backup(reason="backup ao iniciar Horizon")
        cleanup_old_backups()
    except Exception as exc:
        print(f"[HORIZON][AVISO] Backup inicial nao executado: {exc}")

    try:
        from app.security.integrity_service import verify_integrity
        verify_integrity(activate_protected_on_fail=True)
    except Exception as exc:
        print(f"[HORIZON][AVISO] Integrity check inicial nao executado: {exc}")
