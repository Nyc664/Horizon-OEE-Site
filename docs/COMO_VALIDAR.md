# Como validar

## 1. Login

- Deve carregar usuários da tabela `public.usuarios`.
- Não deve aparecer texto sobre senha/hash na tela.
- Senha errada deve mostrar: `Usuário ou senha inválidos.`

## 2. Compatibilidade com EXE

No Supabase, a coluna `usuarios.senha` deve continuar preenchida.

O site pode preencher:

```text
senha_hash
senha_salt
senha_iteracoes
```

mas não deve apagar `senha`.

## 3. Exclusão

Ao excluir:

- pede confirmação;
- pede motivo;
- pede senha novamente;
- não apaga o registro;
- marca `is_deleted = true`;
- grava auditoria;
- grava histórico.

## 4. Erro UUID

O erro abaixo não deve mais aparecer:

```text
invalid input syntax for type uuid: "3"
```

porque `horizon_record_history.record_id` agora é `text`.
