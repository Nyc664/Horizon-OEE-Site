"""
Exemplo de como registrar a camada no main.py do Horizon.
Não substitua seu main.py inteiro sem revisar. Use como referência.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.security_auth_routes import router as security_auth_router
from app.routes.security_admin_routes import router as security_admin_router
# from app.routes.security_registros_example_routes import router as security_registros_router

from app.security.backup_service import create_backup, cleanup_old_backups
from app.security.integrity_service import verify_integrity

app = FastAPI(title="Horizon OEE Web")

app.include_router(security_auth_router)
app.include_router(security_admin_router)
# app.include_router(security_registros_router)  # adaptar antes de usar

app.mount("/security", StaticFiles(directory="web/security"), name="security")

@app.on_event("startup")
def startup_security():
    create_backup(reason="backup ao iniciar Horizon")
    cleanup_old_backups()
    verify_integrity(activate_protected_on_fail=True)

@app.get("/api/health")
def health():
    return {"ok": True}
