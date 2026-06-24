# Como testar com F12 sem enganar a si mesmo

O objetivo não é impedir 100% que alguém abra o F12. Isso é impossível no navegador.
O objetivo é garantir que, mesmo com F12 aberto, a pessoa não consiga burlar o sistema.

## Teste 1 — Mostrar botão escondido

1. Entre como OPERADOR.
2. Abra F12.
3. Encontre um botão de editar escondido por `display:none`.
4. Remova o `display:none`.
5. Clique no botão.

Resultado esperado:

- A tela pode até tentar enviar.
- O backend deve retornar 403.
- A auditoria deve registrar tentativa sem permissão.

## Teste 2 — Chamada manual via console

No console:

```js
fetch('/api/registros/1', {
  method: 'DELETE',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + localStorage.getItem('horizon_access_token')
  },
  body: JSON.stringify({ motivo: 'teste via F12' })
}).then(r => r.text()).then(console.log)
```

Resultado esperado para OPERADOR:

- 403 sem permissão.
- Log na auditoria.

## Teste 3 — Sem token

```js
fetch('/api/security/audit').then(r => console.log(r.status))
```

Resultado esperado:

- 401.

## Teste 4 — Alterar JS localmente

1. No F12, altere funções JS para sempre retornar `true` em permissões.
2. Tente editar/excluir.

Resultado esperado:

- Backend continua bloqueando.

## Teste 5 — Procurar segredo no frontend

Pesquisar no código carregado pelo navegador:

- `service_role`
- `password`
- `secret`
- `supabase`
- chaves longas

Resultado esperado:

- Nenhuma chave secreta real.
- Nenhuma Service Role.
