# Backend

API FastAPI para executar o ambiente visual de “Ancestor-Based alpha-beta Bounds for Monte-Carlo Tree Search”.

O backend compara `UCTαβ` contra `UCT` em um Mini Gomoku determinístico. O motor local fica em `mcts_service.py` e não depende de OpenSpiel.

## Execução

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Rotas

- `GET /api/health`
- `GET /api/simulate?matches=80&simulations=300&c=1.35&c_alpha_beta=1.2&seed=42`
- `GET /api/simulate/stream?matches=80&simulations=300&c=1.35&c_alpha_beta=1.2&seed=42&delay_ms=120`

Parâmetros adicionais:

- `board_size`: tamanho do tabuleiro, de `3` a `7`.
- `win_length`: quantidade em linha para vencer, de `3` a `7`.
