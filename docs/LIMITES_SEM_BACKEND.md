# Limites de segurança sem backend

Esta versão mantém GitHub Pages e Supabase direto no navegador.

Ela melhora muito a operação, mas não substitui backend para segurança industrial total.

## O que fica bom

- Auditoria operacional.
- Hash de senha.
- Bloqueio por falhas.
- Soft delete.
- Motivo e senha crítica.
- Histórico antes/depois.
- Logout por inatividade.

## Limite importante

Como o código roda no navegador, um usuário técnico pode tentar manipular JavaScript.

Para proteção máxima contra F12/API manual, use:

```text
Backend FastAPI
ou
Supabase Auth + RLS bem configurado
```

Sem backend, nunca use `service_role` no frontend.
