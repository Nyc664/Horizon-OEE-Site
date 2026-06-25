# Como validar

## 1. F12 / Sources

Pesquise:

```text
service_role
SUPABASE_SERVICE_ROLE
```

Não pode aparecer.

## 2. Login errado

Erre a senha 5 vezes.

Esperado:
- Mensagem genérica: "Usuário ou senha inválidos."
- Usuário bloqueado temporariamente.
- Evento LOGIN_FAIL na auditoria.

## 3. Inatividade

Faça login e fique 5 minutos sem mexer.

Esperado:
- Logout automático.
- Evento LOGOUT.

## 4. Exclusão segura

Como Admin/Admin Master, tente excluir.

Esperado:
- Confirmação.
- Motivo obrigatório.
- Senha novamente.
- Registro vai para lixeira, não é apagado.
- Evento REGISTRO_SOFT_DELETE.
- Histórico antes/depois.

## 5. Tentativa sem permissão

Como Operador, tente abrir lixeira ou excluir.

Esperado:
- Acesso negado.
- Evento PERMISSION_DENIED.

## 6. Restauração de backup

Só Admin Master deve conseguir restaurar backup JSON.
