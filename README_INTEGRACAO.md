# Horizon OEE Web — Pacote de Segurança Plugável

Este pacote foi criado para encaixar no Horizon Web quando o Codex estiver sem limite.
Ele implementa a base de segurança que o Horizon precisa:

- login com usuário e senha;
- senha com hash seguro;
- perfis de acesso;
- permissões por ação;
- proteção de rotas/API;
- sessão com expiração;
- reautenticação para ações críticas;
- soft delete/lixeira;
- auditoria completa;
- histórico antes/depois;
- backup automático;
- verificação de integridade do SQLite;
- alerta de alteração manual;
- modo protegido;
- base futura para Supabase/RLS sem expor Service Role.

## Como encaixar no Horizon

Copie as pastas abaixo para a raiz do projeto Horizon:

```text
app/security/
app/routes/security_auth_routes.py
app/routes/security_admin_routes.py
app/routes/security_registros_example_routes.py
migrations/001_security_schema.sql
scripts/init_security.py
scripts/create_admin_master.py
scripts/make_backup.py
scripts/run_integrity_check.py
web/security/security-client.js
web/security/security-ui.css
```

## Dependências

Instale no ambiente Python do Horizon:

```bash
pip install -r requirements-security.txt
```

Se o ambiente não permitir instalar nada, o sistema ainda tem fallback de hash PBKDF2 no `password_service.py`, mas o ideal é instalar `argon2-cffi`.

## Configurar caminho do banco

Se o banco do Horizon não for `data/horizon.sqlite`, defina:

```bash
export HORIZON_DB_PATH=/caminho/do/banco.sqlite
```

No Windows `.bat`:

```bat
set HORIZON_DB_PATH=data\horizon.sqlite
```

## Inicializar segurança

Na raiz do projeto:

```bash
python scripts/init_security.py
python scripts/create_admin_master.py
```

O primeiro script cria as tabelas, permissões, backup inicial e marca integridade inicial.
O segundo cria o usuário Admin Master.

## Registrar rotas no FastAPI

No arquivo principal do backend, geralmente `main.py`, `server.py` ou `app/main.py`, adicione:

```python
from app.routes.security_auth_routes import router as security_auth_router
from app.routes.security_admin_routes import router as security_admin_router

app.include_router(security_auth_router)
app.include_router(security_admin_router)
```

Se quiser usar o exemplo de registros:

```python
from app.routes.security_registros_example_routes import router as security_registros_router
app.include_router(security_registros_router)
```

Atenção: a rota de registros é exemplo. Ela assume que existe uma tabela chamada `registros` com coluna `id`. Se o Horizon usa outro nome de tabela, adapte.

## Proteger uma rota existente

Antes:

```python
@app.put('/api/registros/{id}')
def editar(id: str, payload: dict):
    ...
```

Depois:

```python
from fastapi import Depends
from app.security.auth_dependencies import require_permission

@app.put('/api/registros/{id}')
def editar(id: str, payload: dict, user: dict = Depends(require_permission('registros.editar', block_in_protected_mode=True))):
    ...
```

## Registrar auditoria e histórico

Em toda edição/exclusão/restauração:

```python
from app.security.audit_service import audit_log, record_history

audit_log(
    action='registro_editado',
    status='success',
    user=user,
    entity='registros',
    entity_id=id,
    before=antes,
    after=depois,
    reason=motivo,
)

record_history(
    user=user,
    entity='registros',
    entity_id=id,
    action='editar',
    before=antes,
    after=depois,
    reason=motivo,
)
```

## Frontend

Inclua no HTML:

```html
<link rel="stylesheet" href="/security/security-ui.css">
<script src="/security/security-client.js"></script>
<script>
  HorizonSecurity.init({ devtoolsBarrier: true });
</script>
```

Botão visível só para quem pode editar:

```html
<button data-permission="registros.editar">Editar</button>
```

Importante: esconder botão é só UX. A API precisa validar de verdade.

## Login pelo frontend

Exemplo:

```js
await HorizonSecurity.login(emailOuUsuario, senha);
```

Chamando API protegida:

```js
await HorizonSecurity.apiFetch('/api/registros/123', {
  method: 'PUT',
  body: JSON.stringify({ campos: { status: 'Finalizado' }, motivo: 'Correção autorizada' })
});
```

## Ações críticas com senha novamente

```js
const reauthToken = await HorizonSecurity.reauth('registros.soft_delete');
await HorizonSecurity.apiFetch('/api/registros/123', {
  method: 'DELETE',
  body: JSON.stringify({ motivo: 'Registro duplicado', reauth_token: reauthToken })
});
```

## Backup automático ao iniciar

No startup do FastAPI:

```python
from app.security.backup_service import create_backup, cleanup_old_backups
from app.security.integrity_service import verify_integrity

@app.on_event('startup')
def startup_security():
    create_backup(reason='backup ao iniciar sistema')
    cleanup_old_backups()
    verify_integrity(activate_protected_on_fail=True)
```

## Supabase futuramente

Quando usar Supabase:

- usar RLS nas tabelas;
- usar `anon key` com permissão limitada;
- nunca colocar Service Role no frontend;
- ações críticas devem passar pelo backend;
- auditoria deve existir também no banco central.
