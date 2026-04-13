# Ancestor-Based alpha-beta Bounds for MCTS

Este repositório agora contém um ambiente visual para executar e comparar `UCTαβ` contra `UCT`, inspirado no artigo “Ancestor-Based α-β Bounds for Monte-Carlo Tree Search”.

A aplicação usa um Mini Gomoku determinístico como domínio leve de teste. Em cada partida, um agente usa seleção `UCTαβ` e o outro usa `UCT` padrão. O ambiente alterna quem começa, executa um orçamento fixo de simulações por lance e mostra o score acumulado ao longo dos checkpoints.

Para reduzir o ruído dos rollouts aleatórios, ambos os métodos usam a mesma camada tática: jogadas vencedoras imediatas são executadas, ameaças imediatas são bloqueadas e os playouts preferem casas mais centrais. Isso não altera o placar a favor de um método específico, mas dá valores mais estáveis para que os limites ancestrais do `UCTαβ` sejam úteis.

## Componentes principais

- `apps/backend/mcts_service.py`: motor local de MCTS, Mini Gomoku, seleção `UCT`, seleção `UCTαβ`, partidas pareadas e snapshots de comparação.
- `apps/backend/main.py`: API FastAPI com rotas HTTP e streaming via Server-Sent Events.
- `apps/frontend/src/main.jsx`: interface React para configurar a comparação, visualizar score, tabuleiro final e últimos lances.
- `apps/frontend/src/styles.css`: estilos da interface visual.
- `article.txt`: texto do artigo usado como referência para esta adaptação.
- `NM-Method/`: scripts legados do projeto anterior de Negative Momentum/CFR, mantidos como material separado de pesquisa.

## Como executar

Instalação assistida:

```bash
./install.sh
./start.sh
```

Execução manual do backend:

```bash
source .venv/bin/activate
cd apps/backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Execução manual do frontend:

```bash
cd apps/frontend
npm run dev
```

O frontend roda em `http://127.0.0.1:5173` e encaminha chamadas `/api` para `http://127.0.0.1:8000`.

## API

- `GET /api/health`
- `GET /api/simulate`
- `GET /api/simulate/stream`

Parâmetros aceitos em `/api/simulate` e `/api/simulate/stream`:

- `matches`: quantidade de partidas.
- `simulations`: simulações de MCTS por lance.
- `c`: constante de exploração do UCT.
- `c_alpha_beta`: constante usada no ajuste dos limites α-β.
- `seed`: semente do experimento.
- `board_size`: tamanho do tabuleiro, de `3` a `7`.
- `win_length`: quantidade em linha para vencer, de `3` a `7`.
- `delay_ms`: atraso artificial entre checkpoints, apenas no streaming.

Exemplo:

```bash
curl "http://127.0.0.1:8000/api/simulate?matches=40&simulations=200&c=1.35&c_alpha_beta=1.2&seed=42"
```

## Métrica

O score de `UCTαβ` usa:

- vitória: `1`
- empate: `0.5`
- derrota: `0`

O score de `UCT` é o complemento no mesmo conjunto de partidas. A interface mostra o método vencedor pelo maior score acumulado.

## Complexidade

Use a seguinte notação:

- `S`: simulações de MCTS por lance.
- `d`: profundidade média percorrida por simulação.
- `b`: quantidade média de filhos examinados ao escolher um filho, já que a implementação usa `max(...)` sobre os filhos do nó.
- `T`: quantidade de nós armazenados na árvore de busca de um lance.
- `M`: quantidade de partidas.
- `L`: quantidade média de lances por partida.

Por lance:

| Método | Tempo | Espaço |
| --- | --- | --- |
| `UCT` | `O(S · d · b)` | `O(T)` |
| `UCTαβ` | `O(S · d · b)` | `O(T) + O(1)` por simulação |

Na prática, `UCTαβ` mantém a mesma ordem assintótica do `UCT`, mas adiciona custo constante na seleção: atualização dos limites `α`, `β`, `α−`, `β+` e cálculo de `δαβ`/`∆αβ`. Como esses valores são carregados durante a descida e não armazenados em cada nó, o espaço extra é constante por simulação.

Para uma comparação completa com `M` partidas e `L` lances médios por partida, o tempo fica `O(M · L · S · d · b)` para ambos. O espaço máximo continua sendo o da árvore de um lance, `O(T)`, porque a árvore é recriada a cada decisão.

## Observação

A implementação em `apps/backend/mcts_service.py` é uma adaptação prática para experimentação local. Ela segue a ideia do artigo de usar limites ancestrais α e β para modular a exploração durante a seleção MCTS, mas não tenta reproduzir exatamente o framework experimental em Cython usado pelos autores.
