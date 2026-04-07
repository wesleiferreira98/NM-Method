# Backend

API separada dos arquivos originais de pesquisa em `NM-Method/`.

Ela expõe uma simulação de Kuhn Poker com CFR e momento negativo para alimentar o frontend. O modo padrão chama o fork do paper por meio de `paper_bridge.py`.

O modo didático também continua disponível e chama diretamente a adaptação `NM-Method/Kuhn_Poker_CFR-style_MoCFR.py` por meio de `kuhn_service.py`. O modo paper depende de `pyspiel`, `open_spiel`, `numpy` e `attrs`.

## Execução

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Rotas

- `GET /api/health`
- `GET /api/paper/status`
- `GET /api/simulate?iterations=2000&mu=0.01&interval=200&seed=42`
- `GET /api/simulate?iterations=2000&mu=0.01&interval=200&seed=42&mode=educational`
- `GET /api/simulate/stream?iterations=2000&mu=0.01&interval=200&seed=42&delay_ms=120`
- `GET /api/simulate/stream?iterations=2000&mu=0.01&interval=200&seed=42&mode=educational&delay_ms=120`
