# Horizon OEE — PTH/WAVE completo usando public.usuarios

Este pacote é a versão completa sem backend, mantendo o conceito de GitHub Pages.

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
  001_horizon_static_completo_usuarios_existente.sql
docs/
  COMO_SUBIR.md
  COMO_VALIDAR.md
  COMPATIBILIDADE_EXE.md
```

## Pontos principais

- Usa a tabela existente `public.usuarios`.
- Não cria `horizon_users`.
- Não apaga nem altera `usuarios.senha`.
- O EXE continua podendo usar a coluna `senha`.
- O site cria `senha_hash` separado quando o login dá certo.
- Sessão expira após 5 minutos sem atividade.
- Bloqueio após várias falhas.
- Lixeira/soft delete.
- Exclusão com confirmação, motivo e senha.
- Auditoria de ações e tentativas negadas.
- Histórico antes/depois.
- Backup JSON e restauração somente Admin Master.

## Passos

1. Suba o pacote no GitHub.
2. Rode o SQL em `supabase/001_horizon_static_completo_usuarios_existente.sql`.
3. Abra o GitHub Pages com Ctrl + F5.
