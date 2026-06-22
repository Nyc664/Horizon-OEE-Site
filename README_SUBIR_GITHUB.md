# Horizon OEE — PTH/WAVE com Supabase

## O que este pacote faz

Esta versão cria uma tela PTH/WAVE separada do Horizon original.

Ela usa a tabela nova:

```text
public.downtime_pth_wave
```

E NÃO altera a tabela original:

```text
public.downtime
```

## Arquivos

- `01_create_downtime_pth_wave.sql`
  - Cria a tabela nova no Supabase.
  - Cria índices.
  - Ativa RLS.
  - Cria policies para o protótipo funcionar via GitHub Pages.

- `index.html`
  - Site PTH/WAVE conectado ao Supabase.
  - Tablet e PC passam a enxergar os mesmos registros.
  - Formulário de chamado abre somente ao clicar em `+ Novo Registro`.

- `config.json`
  - Guarda informações fixas:
    - URL do Supabase;
    - publishable key;
    - nome da tabela nova;
    - linhas PTH/Wave;
    - motivos;
    - tempo de atualização automática.

## Passo 1 — Criar a tabela no Supabase

No Supabase:

1. Abra o projeto:
   `abmlvlkkflxzvcciwawz`

2. Vá em:

```text
SQL Editor > New query
```

3. Cole o conteúdo do arquivo:

```text
01_create_downtime_pth_wave.sql
```

4. Clique em:

```text
Run
```

## Passo 2 — Subir no GitHub Pages

No repositório do site, envie para a raiz:

```text
index.html
config.json
```

Pode manter o `README.md`.

Depois clique em:

```text
Commit changes
```

Aguarde o GitHub Pages atualizar.

## Como testar

1. Abra o site no tablet.
2. Clique em `+ Novo Registro`.
3. Salve uma parada.
4. Abra o mesmo site no PC.
5. Aguarde até 5 segundos ou atualize a página.
6. O registro deve aparecer no PC.

## Segurança

Esta versão é para protótipo/controlado.

Como o GitHub Pages é público, a publishable key fica no `config.json`.
Isso é aceitável para protótipo desde que a tabela tenha RLS, mas as policies deste pacote permitem escrita pública para o sistema funcionar sem login.

Para produção, o ideal é adicionar login e restringir as policies por usuário/perfil.

NUNCA coloque no GitHub:

```text
service_role key
senha do banco
DATABASE_URL com senha real
```
