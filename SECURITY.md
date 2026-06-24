# SECURITY — Horizon OEE Web

## Princípio principal

O frontend não é confiável.

HTML, CSS e JavaScript servem para interface. Qualquer pessoa pode abrir F12, alterar JavaScript, chamar API manualmente ou esconder/mostrar botões. Por isso, toda regra crítica precisa estar no backend e no banco.

## O que foi implementado neste pacote

### Login

- Usuário/e-mail e senha.
- Usuário ativo/inativo.
- Bloqueio após falhas.
- Auditoria de login bem-sucedido e falho.

### Senhas

- Preferência por Argon2id via `argon2-cffi`.
- Fallback com PBKDF2-HMAC-SHA256, salt único e 600.000 iterações.
- Senha pura nunca deve ser salva.

### Perfis

- `OPERADOR`
- `ADMIN`
- `ADMIN_MASTER`

### Permissões por ação

Exemplos:

- `registros.visualizar`
- `registros.criar`
- `registros.editar`
- `registros.soft_delete`
- `registros.restaurar`
- `registros.delete_definitivo`
- `usuarios.criar`
- `backup.restaurar`
- `auditoria.visualizar`

### Sessão

- Token Bearer.
- Token salvo no banco como hash.
- Expiração total.
- Expiração por inatividade.
- Revogação no logout.

### Reautenticação

Ações críticas podem pedir senha novamente e gerar token temporário de reautenticação.

### Auditoria

Tabela `security_audit_logs` registra:

- usuário;
- perfil;
- ação;
- entidade;
- status;
- motivo;
- antes/depois;
- IP;
- user-agent;
- detalhes.

### Histórico antes/depois

Tabela `security_record_history` registra alterações importantes por entidade e ID.

### Soft delete

A exclusão lógica marca:

- `deleted_at`
- `deleted_by`
- `delete_reason`

Restauração marca:

- `restored_at`
- `restored_by`
- `restore_reason`

Exclusão definitiva deve ser somente Admin Master.

### Backup

- Backup SQLite usando API segura do SQLite.
- Registro em tabela.
- SHA-256 do arquivo.
- Retenção configurável.

### Integridade

- `PRAGMA integrity_check`.
- Hash/checksum de tabelas críticas.
- Divergência ativa modo protegido.

### Modo protegido

Bloqueia ações críticas quando há risco de integridade.
Admin Master pode analisar e desativar.

## O que não deve ser feito

- Não colocar Service Role no frontend.
- Não colocar senha no HTML/JS.
- Não validar permissão só escondendo botão.
- Não apagar registro direto sem auditoria.
- Não deixar rota crítica sem `require_permission`.
- Não confiar em proteção contra F12.

## Sobre F12

Este pacote inclui uma barreira leve de F12 no frontend, mas isso não é segurança real. A proteção verdadeira está nas permissões do backend.

## Sobre Supabase

Quando migrar:

- ativar RLS;
- criar políticas por perfil/usuário;
- usar Service Role somente no backend;
- manter auditoria;
- não deixar ação crítica direto no navegador.
