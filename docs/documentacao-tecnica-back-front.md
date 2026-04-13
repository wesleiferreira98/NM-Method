# Documentação técnica do backend e frontend

Este documento descreve a aplicação visual de comparação entre `UCTαβ` e `UCT`.

## Estrutura

- `apps/backend/main.py`: declara a API FastAPI, CORS e rotas de simulação.
- `apps/backend/mcts_service.py`: contém Mini Gomoku, MCTS, seleção UCT, seleção UCTαβ e agregação de resultados.
- `apps/frontend/src/main.jsx`: consome o streaming da API e renderiza controles, métricas, gráfico, tabuleiro e lances.
- `apps/frontend/src/styles.css`: estilos da interface.

Os arquivos em `NM-Method/` permanecem como legado do projeto anterior e não são usados pela aplicação visual atual.

## Backend

### `SimulationConfig`

Configuração aceita pelo motor:

- `matches`
- `simulations`
- `c`
- `c_alpha_beta`
- `seed`
- `board_size`
- `win_length`

### Rotas

`GET /api/health` retorna:

```json
{
  "status": "ok"
}
```

`GET /api/simulate` executa a comparação inteira e retorna o último snapshot.

`GET /api/simulate/stream` executa a comparação com Server-Sent Events. Cada checkpoint é enviado como:

```text
data: {...json...}
```

Se ocorrer erro, a rota envia:

```text
event: stream-error
data: {"error": "...", "done": true}
```

## Motor MCTS

O ambiente usa Mini Gomoku em tabuleiro configurável. Cada estado guarda:

- tabuleiro;
- jogador da vez;
- tamanho do tabuleiro;
- quantidade em linha para vencer.

Cada partida alterna os métodos:

- `UCTαβ` joga por um lado;
- `UCT` joga pelo outro;
- na partida seguinte, quem começa é invertido.

O score de `UCTαβ` é:

- vitória: `1`
- empate: `0.5`
- derrota: `0`

O score de `UCT` é o complemento no mesmo conjunto de partidas.

## Playouts

Ambos os métodos recebem a mesma política tática leve:

- se o jogador da vez tem vitória imediata, ele joga essa ação;
- se o oponente tem ameaça imediata, o jogador bloqueia;
- nos playouts, a escolha continua estocástica, mas prefere casas mais centrais.

Essa camada reduz ruído nos valores estimados sem alterar o critério de pontuação. O objetivo é criar um domínio mais favorável ao uso dos limites ancestrais, como no espírito dos experimentos do artigo, que também usam playouts informados e outras melhorias de MCTS.

## UCTαβ

A implementação local mantém a estrutura MCTS tradicional:

1. Seleção.
2. Expansão.
3. Playout aleatório.
4. Backpropagation.

Na seleção, o UCT padrão usa média do filho mais bônus de exploração. O `UCTαβ` calcula limites α e β durante a descida com base nos ancestrais já escolhidos e usa esses limites para alterar o termo de exploração. Quando os limites ainda não estão definidos ou produzem um ajuste inválido, a seleção volta para UCT padrão naquele passo.

## Complexidade

Notação usada:

- `S`: simulações de MCTS por lance.
- `d`: profundidade média de cada simulação.
- `b`: quantidade média de filhos examinados na seleção de um nó.
- `T`: quantidade de nós guardados na árvore de busca de um lance.
- `M`: quantidade de partidas.
- `L`: quantidade média de lances por partida.

### UCT

Tempo por lance: `O(S · d · b)`.

Cada simulação percorre a árvore, escolhe filhos com uma varredura pelos filhos do nó, expande quando necessário, executa playout e faz backpropagation. A parte dominante na seleção é a busca do melhor filho por `max(...)`.

Espaço por lance: `O(T)`.

A árvore guarda os nós visitados, suas estatísticas, filhos e ações ainda não exploradas.

### UCTαβ

Tempo por lance: `O(S · d · b)`.

A ordem assintótica permanece igual à do UCT porque a seleção continua varrendo os filhos do nó. O método adiciona custo constante por passo de seleção para atualizar `α`, `β`, `α−`, `β+` e calcular o ajuste `δαβ`/`∆αβ`.

Espaço por lance: `O(T) + O(1)` por simulação.

Os limites ancestrais são variáveis temporárias da descida atual. Eles não são persistidos nos nós, então o crescimento de memória continua dominado pela árvore MCTS.

### Comparação completa

Para `M` partidas com `L` lances médios, ambos executam:

```text
O(M · L · S · d · b)
```

O espaço máximo permanece `O(T)` por decisão, pois a implementação recria a árvore a cada lance.

## Contrato do snapshot

Campos principais retornados:

```json
{
  "game": "Mini Gomoku 5x5",
  "method": "Ancestor-Based alpha-beta Bounds for MCTS",
  "source": "local-mcts",
  "config": {},
  "timeline": [],
  "comparison": {},
  "finalScore": 0.55,
  "wins": 20,
  "draws": 3,
  "lastMatch": {},
  "progress": 1,
  "currentIteration": 80,
  "done": true
}
```

Cada ponto de `timeline` contém:

- `iteration`: número da partida no checkpoint.
- `score`: score acumulado de `UCTαβ`.
- `winRate`: taxa de vitórias de `UCTαβ`.
- `uctScore`: score acumulado de `UCT`.
- `uctWinRate`: taxa de vitórias de `UCT`.
- `drawRate`: taxa de empates.
- `alphaBetaWins`, `uctWins`, `draws`: contagens acumuladas.

## Frontend

O frontend abre um `EventSource` para `/api/simulate/stream`, atualiza o estado a cada checkpoint e renderiza:

- cartões de score;
- barra de progresso;
- gráfico SVG;
- lista de checkpoints;
- tabuleiro da última partida;
- últimos lances.

O Vite encaminha chamadas `/api` para `http://127.0.0.1:8000`.
