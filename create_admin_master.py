"""
Cria o primeiro Admin Master.
Uso:
  python scripts/create_admin_master.py
"""
import getpass
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.security.user_service import create_user, get_user_by_login
from app.security.permissions import seed_default_permissions
from app.security.audit_service import audit_log


def main():
    seed_default_permissions()
    username = input("Usuário Admin Master [admin.master]: ").strip() or "admin.master"
    if get_user_by_login(username):
        print("Este usuário já existe.")
        return
    display_name = input("Nome exibido [Admin Master]: ").strip() or "Admin Master"
    email = input("E-mail (opcional): ").strip() or None
    while True:
        p1 = getpass.getpass("Senha forte: ")
        p2 = getpass.getpass("Confirmar senha: ")
        if p1 != p2:
            print("As senhas não conferem.")
            continue
        if len(p1) < 8:
            print("A senha precisa ter pelo menos 8 caracteres.")
            continue
        break
    user = create_user(username=username, display_name=display_name, password=p1, role="ADMIN_MASTER", email=email)
    audit_log(action="admin_master_criado", status="success", user={"id": user["id"], "username": user["username"], "role": user["role"]})
    print("Admin Master criado com sucesso.")

if __name__ == "__main__":
    main()
