# Horizon OEE — PTH/WAVE com Login pela tabela usuarios

## Ordem correta

1. No Supabase, execute:

```text
02_login_usuarios_pth_wave.sql
```

2. No GitHub, substitua/suba na raiz:

```text
index.html
config.json
```

3. Faça commit e aguarde GitHub Pages atualizar.

## O que muda

- O site agora abre com tela de login.
- O login usa a tabela existente:

```text
public.usuarios
```

- O site salva auditoria na tabela nova:

```text
public.downtime_pth_wave
```

Campos adicionados à tabela nova:
- criado_por_id
- criado_por_nome
- criado_por_email
- atualizado_por_id
- atualizado_por_nome
- atualizado_por_email
- finalizado_por_id
- finalizado_por_nome
- finalizado_por_email

## Proteção

A tabela original do Horizon:

```text
public.downtime
```

não é alterada.
