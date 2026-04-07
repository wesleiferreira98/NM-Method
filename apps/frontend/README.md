# Frontend

Interface React separada dos arquivos originais de pesquisa em `NM-Method/`.

Ela consome a API em `apps/backend` para exibir uma versão visual de Kuhn Poker treinada com momento negativo.

## Execução

```bash
npm install
npm run dev
```

O servidor Vite usa `http://127.0.0.1:5173` e encaminha chamadas `/api` para `http://127.0.0.1:8000`.
