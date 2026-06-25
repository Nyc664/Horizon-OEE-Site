# Patch para usar a tabela existente `public.usuarios`

Você estava certo: o sistema não precisa da tabela `horizon_users`.

Este patch substitui:

```text
web/js/config.js
web/js/app.js
```

E adiciona o SQL:

```text
supabase/004_patch_usar_tabela_usuarios_existente.sql
```

## Como aplicar

1. Substitua os arquivos `web/js/config.js` e `web/js/app.js` no GitHub.
2. Rode o SQL no Supabase SQL Editor.
3. Faça Commit & Push.
4. Abra o site com Ctrl + F5.

## Campos esperados em `public.usuarios`

```text
id
nome
email
senha
setor
role
ativo
```

O SQL adiciona campos novos para hash e bloqueio:

```text
senha_hash
senha_salt
senha_iteracoes
failed_login_count
locked_until
last_login_at
```

No primeiro login correto, se o usuário ainda estiver usando senha antiga em texto, o sistema cria o hash PBKDF2 e passa a usar hash nos próximos logins.
