# HOTFIX 006 — erro UUID ao excluir

## Erro

```text
Erro ao excluir: invalid input syntax for type uuid: "3"
```

## Causa

O registro usa ID de usuário numérico vindo de `public.usuarios.id`, exemplo:

```text
3
```

Mas alguma coluna da tabela `downtime_pth_wave` provavelmente ficou como `uuid`, exemplo:

```text
deleted_by uuid
```

Ao excluir, o site tenta gravar:

```text
deleted_by = 3
```

e o Supabase acusa erro de UUID.

## Correção

Rode no Supabase SQL Editor:

```text
supabase/006_hotfix_downtime_uuid_para_text.sql
```

## Depois

1. Volte no GitHub Pages.
2. Aperte Ctrl + F5.
3. Teste excluir de novo.

## Segurança

Este hotfix:

- não apaga dados;
- não muda `usuarios.senha`;
- não quebra o EXE;
- só converte campos de rastreabilidade para `text`.
