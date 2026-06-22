# Horizon OEE — Site PTH/WAVE

Protótipo em HTML puro para registros de parada da linha PTH/WAVE.

## Arquivos

- `index.html` — arquivo principal do site.
- HTML, CSS e JavaScript estão juntos no mesmo arquivo.
- Não precisa de backend.
- Não precisa de banco.
- Não precisa de instalação.

## Funções atuais

- Criar novo registro de parada.
- Linhas: PTH/Wave 1 e PTH/Wave 2.
- Motivos: Manutenção, Parada por Processo, Setup, Falta de Material e Qualidade.
- Data automática.
- Hora início automática.
- Hora fim automática ao finalizar.
- Bloqueia novo chamado se já existir um em abertura.
- Finalização com confirmação.
- Opção de apagar registro selecionado.
- Paginação só aparece acima de 20 registros.
- Dados ficam salvos localmente no navegador via `localStorage`.

## Como publicar no GitHub Pages

1. Crie um repositório no GitHub.
2. Envie o arquivo `index.html` para a raiz do repositório.
3. Acesse: Settings > Pages.
4. Em Source, selecione:
   - Deploy from a branch
   - Branch: main
   - Folder: /root
5. Clique em Save.
6. O GitHub vai gerar um link para acessar o site.

## Observação

Este protótipo ainda não envia dados reais para o Horizon, API ou Supabase.
A integração futura deve ser feita no JavaScript, na função preparada para envio.
