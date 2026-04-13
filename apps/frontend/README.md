# Frontend

Interface React/Vite para visualizar a comparação entre `UCTαβ` e `UCT`.

A tela consome a API em `apps/backend`, mostra o score acumulado, os checkpoints da comparação, o tabuleiro final da última partida e os últimos lances jogados.

## Execução

```bash
npm install
npm run dev
```

O servidor Vite usa `http://127.0.0.1:5173` e encaminha chamadas `/api` para `http://127.0.0.1:8000`.
