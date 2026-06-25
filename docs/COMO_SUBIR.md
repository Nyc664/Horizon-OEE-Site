# Como subir no GitHub

Na raiz do repositório deixe:

```text
index.html
README.md
web/
supabase/
docs/
```

Apague versões antigas soltas que não estejam nessas pastas.

Depois faça commit:

```text
Atualizar Horizon Static com segurança operacional
```

## Configuração

Edite:

```text
web/js/config.js
```

Preencha:

```js
supabaseUrl: "https://xxxx.supabase.co",
supabaseAnonKey: "sua anon public key"
```

Nunca coloque `service_role`.
