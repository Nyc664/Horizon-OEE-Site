# Horizon OEE — PTH/WAVE Static com Segurança Operacional

Este pacote mantém o conceito de site pelo GitHub Pages, sem backend Python.

## Estrutura

```text
index.html
README.md
web/
  css/horizon.css
  js/config.js
  js/security.js
  js/app.js
supabase/
  001_static_security_schema.sql
docs/
  COMO_SUBIR.md
  COMO_VALIDAR.md
  LIMITES_SEM_BACKEND.md
```

## O que foi adicionado

- Sessão cai após 5 minutos sem atividade.
- Senha com hash PBKDF2-SHA256 usando WebCrypto.
- Bloqueio após várias falhas de login.
- Mensagem genérica de erro de login.
- Senha novamente para ações críticas.
- Confirmação antes de ações críticas.
- Exclusão segura com motivo.
- Soft delete para lixeira.
- Lixeira no menu de 3 linhas.
- Registro de tentativas sem permissão.
- Registro de quem editou/excluiu/restaurou.
- Histórico antes/depois.
- Backup JSON e restauração somente Admin Master.

## Passos

1. Suba os arquivos para o GitHub.
2. No Supabase, rode `supabase/001_static_security_schema.sql`.
3. Edite `web/js/config.js` com sua URL e anon key do Supabase.
4. Abra o GitHub Pages.
5. Clique em "Criar Admin Master inicial".
6. Faça login e teste.
