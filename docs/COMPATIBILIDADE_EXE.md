# Compatibilidade com Horizon EXE

Este pacote foi feito para não quebrar o EXE.

## Não mexe no que o EXE usa

Não remove:

```text
public.usuarios.senha
public.usuarios.nome
public.usuarios.email
public.usuarios.role
public.usuarios.setor
```

## O que adiciona

Adiciona colunas novas:

```text
senha_hash
senha_salt
senha_algoritmo
senha_iteracoes
failed_login_count
locked_until
last_login_at
```

O EXE pode ignorar essas colunas.

## Atenção futura

Quando atualizar o EXE, ele deve passar a respeitar:

```text
is_deleted
locked_until
senha_hash
auditoria
```

Mas agora ele continua usando `usuarios.senha`.
