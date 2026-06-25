# Correção para abrir http://127.0.0.1:8000

O backend precisa do arquivo `backend/app/main.py`.

## Como aplicar

Copie estes arquivos para o projeto, mantendo os caminhos:

```text
backend/app/main.py
backend/INICIAR_HORIZON_SEGURO.bat
backend/TESTAR_BACKEND.bat
backend/requirements.txt
backend/README_ABRIR_LOCALHOST.md
```

## Como abrir

Clique duas vezes em:

```text
backend/INICIAR_HORIZON_SEGURO.bat
```

Quando aparecer `Uvicorn running on http://127.0.0.1:8000`, abra:

```text
http://127.0.0.1:8000
```

`127.0.0.1` só funciona no mesmo PC onde o backend está rodando.
