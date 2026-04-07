# Documentação técnica do backend e frontend

Este documento descreve como o backend e o frontend da aplicação visual estão organizados em termos de código, fluxo de dados e integração entre as camadas.

## Estrutura geral

A aplicação visual fica separada dos scripts de pesquisa originais:

- `apps/backend/`: API em Python com FastAPI.
- `apps/frontend/`: interface React servida pelo Vite.
- `NM-Method/`: scripts de pesquisa e implementações dos algoritmos, incluindo a adaptação usada pela API didática.

O backend é responsável por executar o treinamento, transformar o resultado em JSON e expor endpoints HTTP. O frontend é responsável por coletar parâmetros do usuário, chamar a API, receber snapshots em tempo real e renderizar os gráficos e painéis.

## Backend

### Arquivos principais

- `apps/backend/main.py`: define a aplicação FastAPI, configura CORS e declara as rotas públicas.
- `apps/backend/kuhn_service.py`: carrega dinamicamente a adaptação didática de Kuhn Poker e fornece funções de treino para o backend.
- `apps/backend/paper_bridge.py`: integra opcionalmente o solver do fork do paper, quando `pyspiel`, `open_spiel`, `numpy` e `attrs` estão disponíveis.
- `apps/backend/requirements.txt`: lista as dependências mínimas da API.

### Aplicação FastAPI

O arquivo `main.py` cria a aplicação com:

```text
FastAPI(title="NM Method Poker API", version="0.1.0")
```

Ele também configura CORS para permitir chamadas vindas do frontend local:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Isso permite que o frontend em desenvolvimento acesse a API em `127.0.0.1:8000` sem bloqueio do navegador.

### Rotas da API

#### `GET /api/health`

Rota simples de saúde da API.

Resposta esperada:

```json
{
  "status": "ok"
}
```

#### `GET /api/paper/status`

Verifica se o modo `paper` pode ser usado no ambiente atual.

Internamente, chama `check_paper_availability()` em `paper_bridge.py`. Essa função valida se o diretório `NM-Method/` existe e tenta importar as dependências exigidas pelo modo paper:

- `attr`
- `numpy`
- `pyspiel`
- `open_spiel.python.algorithms.exploitability`

Resposta quando disponível:

```json
{
  "available": true,
  "reason": null
}
```

Resposta quando indisponível:

```json
{
  "available": false,
  "reason": "Dependencia ausente: pyspiel"
}
```

#### `GET /api/simulate`

Executa a simulação e retorna o resultado completo apenas ao final.

Parâmetros aceitos:

- `iterations`: quantidade de iterações, de `50` a `50000`.
- `mu`: valor do momento negativo, de `0.0` a `1.0`.
- `interval`: intervalo usado para atualizar a referência de arrependimentos, de `1` a `10000`.
- `seed`: semente da simulação, de `0` a `1000000`.
- `mode`: `educational` ou `paper`.

Quando `mode=educational`, a rota chama `train_kuhn(config)`.

Quando `mode=paper`, a rota chama `run_paper_mocfr(config)`. Se o modo paper estiver indisponível, a API retorna erro HTTP `503`.

#### `GET /api/simulate/stream`

Executa a simulação em modo streaming usando Server-Sent Events.

Essa é a rota principal usada pelo frontend. Ela envia snapshots parciais durante o treinamento, em vez de esperar tudo terminar.

Parâmetros aceitos:

- `iterations`
- `mu`
- `interval`
- `seed`
- `mode`
- `delay_ms`: atraso artificial entre snapshots, de `0` a `2000` milissegundos.

O backend retorna uma `StreamingResponse` com `media_type="text/event-stream"`.

Cada snapshot é enviado no formato:

```text
data: {...json...}
```

Se ocorrer um erro durante o streaming, o backend envia um evento customizado:

```text
event: stream-error
data: {"error": "...", "done": true}
```

### Configuração da simulação

O objeto `SimulationConfig`, definido em `kuhn_service.py`, centraliza os parâmetros usados pelas rotas:

```text
iterations
mu
interval
seed
```

O backend usa esse objeto tanto no modo didático quanto no modo paper, mantendo o contrato das rotas consistente.

### Modo didático

O modo didático é implementado em `kuhn_service.py`.

Ele carrega dinamicamente o arquivo:

```text
NM-Method/Kuhn_Poker_CFR-style_MoCFR.py
```

Esse carregamento usa `importlib.util.spec_from_file_location`, porque o nome do arquivo contém hífen e não é um módulo Python importável de forma convencional.

As funções principais são:

- `load_kuhn_adaptation()`: carrega o módulo adaptado e usa cache com `lru_cache`.
- `train_kuhn(config)`: executa a simulação completa e retorna o resultado final.
- `stream_kuhn(config)`: repassa os snapshots gerados pela adaptação.
- `action_label(history, action_index)`: converte índices de ação em rótulos usados na resposta.

No modo didático, o backend fixa `n_cards=3`, representando o Kuhn Poker com `J`, `Q` e `K`.

### Adaptação didática de Kuhn Poker

O arquivo `NM-Method/Kuhn_Poker_CFR-style_MoCFR.py` contém a lógica de treino usada pelo modo didático.

Ele define:

- `RunConfig`: configuração do treinamento.
- `regret`: armazenamento global dos arrependimentos.
- `strategy_sum`: acumulador da estratégia média.
- `regret_matching()`: converte arrependimentos positivos em probabilidades de ação.
- `cfr()`: percorre recursivamente o jogo, atualiza arrependimentos e aplica o termo de momento negativo.
- `average_strategy()`: calcula a estratégia média.
- `compute_exploitability()`: calcula a exploitability da estratégia média.
- `iter_structured_snapshots()`: gera snapshots estruturados para o streaming.
- `run_structured()`: retorna o resultado final em formato JSON-friendly.

O contrato produzido por `run_structured()` e `iter_structured_snapshots()` inclui campos como:

```json
{
  "game": "Kuhn Poker",
  "method": "Kuhn CFR-style MoCFR",
  "source": "educational",
  "config": {
    "iterations": 2000,
    "mu": 0.01,
    "interval": 200,
    "seed": 42,
    "nCards": 3
  },
  "timeline": [
    {
      "iteration": 1,
      "exploitability": 0.875
    }
  ],
  "finalExploitability": 0.023451,
  "decisions": [],
  "progress": 1,
  "currentIteration": 2000,
  "done": true
}
```

No retorno final de `/api/simulate`, os campos `progress`, `currentIteration` e `done` podem não aparecer, porque eles são mais importantes no fluxo de streaming.

### Estrutura de `decisions`

O campo `decisions` é usado pelo frontend para renderizar a estratégia aprendida.

Cada decisão segue o formato:

```json
{
  "key": "P1:K:inicio",
  "player": 1,
  "card": "K",
  "history": "inicio",
  "checkCall": 0.25,
  "betRaise": 0.75,
  "recommendedAction": "bet"
}
```

Os campos principais são:

- `player`: jogador associado à decisão.
- `card`: carta do jogador.
- `history`: ponto do jogo em que a decisão acontece.
- `checkCall`: probabilidade da primeira ação.
- `betRaise`: probabilidade da segunda ação.
- `recommendedAction`: ação de maior probabilidade.

### Modo paper

O modo paper é implementado em `paper_bridge.py`.

Ele adiciona `NM-Method/` ao `sys.path` e importa:

- `MoCFR`
- `pyspiel`
- `open_spiel.python.algorithms.exploitability`

Depois carrega o jogo com:

```text
pyspiel.load_game("kuhn_poker")
```

O solver usado é:

```text
MoCFR.CFRPlusSolver(game, itv=config.interval, mu=config.mu)
```

Durante o treinamento, o backend chama `solver.evaluate_and_update_policy()` e calcula a convergência com `exploitability.nash_conv(game, solver.current_policy())`.

Como o formato das chaves do OpenSpiel é diferente do formato da adaptação didática, `paper_bridge.py` normaliza cartas, históricos e decisões para entregar ao frontend um contrato parecido com o modo didático.

## Frontend

### Arquivos principais

- `apps/frontend/src/main.jsx`: contém a aplicação React, estado da tela, chamadas à API, gráfico SVG e renderização dos painéis.
- `apps/frontend/src/styles.css`: define layout, cores, responsividade, cards, gráfico e barras de estratégia.
- `apps/frontend/vite.config.js`: configura Vite, React e proxy para a API.
- `apps/frontend/package.json`: define scripts e dependências do frontend.

### Configuração Vite

O Vite roda na porta `5173` e encaminha chamadas `/api` para o backend:

```text
/api -> http://127.0.0.1:8000
```

Com isso, o frontend pode chamar:

```text
/api/simulate/stream
/api/paper/status
```

sem precisar escrever a URL completa do backend.

### Dependências e scripts

O frontend usa:

- `react`
- `react-dom`
- `vite`
- `@vitejs/plugin-react`

Scripts principais:

- `npm run dev`: inicia o servidor de desenvolvimento.
- `npm run build`: gera build de produção.
- `npm run preview`: serve localmente o build gerado.

### Estado principal da aplicação

O componente `App` centraliza o estado da interface.

Estados principais:

- `params`: parâmetros da simulação, como iterações, `mu`, intervalo, seed, modo e delay.
- `data`: último snapshot ou resultado recebido da API.
- `status`: estado da tela, como `idle`, `loading`, `streaming`, `ready` ou `error`.
- `error`: mensagem de erro exibida ao usuário.
- `paperStatus`: disponibilidade do modo paper.
- `selectedCard`: carta selecionada na estratégia aprendida.
- `selectedPlayer`: jogador selecionado na estratégia aprendida.
- `eventSourceRef`: referência para a conexão SSE ativa.

Os parâmetros iniciais ficam em `DEFAULT_PARAMS`:

```text
iterations: 2000
mu: 0.01
interval: 200
seed: 42
mode: "educational"
delayMs: 120
```

### Inicialização da tela

Quando o componente monta, o `useEffect` executa duas ações:

1. Inicia uma simulação com `DEFAULT_PARAMS`.
2. Consulta `/api/paper/status` para verificar se o modo paper está disponível.

No encerramento do componente, o frontend chama `closeStream()` para fechar qualquer conexão SSE aberta.

### Fluxo de streaming

O frontend usa `EventSource` para consumir `/api/simulate/stream`.

O fluxo é:

1. `runSimulation()` fecha qualquer stream anterior.
2. Define `status` como `loading`.
3. Limpa erro e dados anteriores.
4. Chama `runSimulationStream(nextParams)`.
5. `runSimulationStream()` monta a query string com `URLSearchParams`.
6. Cria um `EventSource` apontando para `/api/simulate/stream`.
7. A cada mensagem recebida, parseia o JSON e atualiza `data`.
8. Se o snapshot vier com `done: true`, fecha a conexão.

Erros do backend enviados como `stream-error` atualizam `error`, limpam `data` e colocam `status` como `error`.

Erros genéricos de conexão também fecham a stream e exibem a mensagem:

```text
A conexão em tempo real foi interrompida.
```

### Construção da query string

O frontend transforma os parâmetros da interface em query string com `buildQuery()`.

Campos enviados:

- `iterations`
- `mu`
- `interval`
- `seed`
- `mode`
- `delay_ms`

O nome `delay_ms` segue o parâmetro esperado pela rota FastAPI.

### Atualização dos parâmetros

A função `updateParam(name, value)` atualiza os parâmetros numéricos.

Ela trata `mu` como número decimal e os demais parâmetros numéricos como inteiros.

A função `updateMode(mode)` troca entre `educational` e `paper` e já dispara uma nova simulação com o modo escolhido.

### Filtro da estratégia aprendida

O frontend recebe todas as decisões no campo `data.decisions`.

Depois usa `selectedCard` e `selectedPlayer` para filtrar apenas as decisões relevantes:

```text
decision.card === selectedCard
decision.player === selectedPlayer
```

Esse filtro alimenta a lista de decisões exibida na seção de estratégia aprendida.

### Gráfico de convergência

O gráfico é um SVG criado diretamente em React, sem biblioteca externa.

A função `getChartGeometry(points)` calcula:

- dimensões do SVG;
- área útil do gráfico;
- maior valor de exploitability;
- coordenadas `x` e `y` de cada ponto;
- caminho da linha;
- caminho da área preenchida abaixo da linha.

A função `gridLines(chart)` gera as linhas de grade com cinco marcadores proporcionais ao valor máximo de exploitability.

O componente `Chart` renderiza:

- superfície do gráfico;
- linhas de grade;
- eixos;
- área preenchida;
- linha de convergência;
- pontos de checkpoint;
- marcador do ponto mais recente;
- labels dos eixos.

### Layout e CSS

O CSS usa uma estrutura de grid para organizar a tela:

- `.app-shell`: container geral.
- `.hero`: cabeçalho com imagem de fundo e métrica de iteração.
- `.simulation-grid`: coluna de configuração e painel principal.
- `.details-grid`: lista de checkpoints e estratégia aprendida.
- `.control-panel`, `.monitor-panel`, `.timeline-panel`, `.strategy-panel`: cards principais.

As seções usam bordas, fundo branco, raio de `8px` e tons de verde para destacar estado ativo, progresso e curva do gráfico.

O gráfico é estilizado por classes como:

- `.chart-frame`
- `.chart-line`
- `.chart-area`
- `.chart-dot`
- `.latest-marker`

As barras da estratégia aprendida usam:

- `.bars span`
- `.bars span + span`

A primeira barra representa `Check/Call`, e a segunda representa `Bet/Raise`.

### Responsividade

O CSS possui dois breakpoints principais:

- Até `900px`: hero, grids e linha de status passam para uma coluna; o título do hero diminui; o cabeçalho da estratégia vira coluna.
- Até `560px`: o padding geral da página e dos painéis é reduzido.

Isso permite que a interface continue utilizável em telas menores.

## Contrato entre backend e frontend

O frontend espera que cada snapshot da API tenha, no mínimo, estes campos:

```json
{
  "source": "educational",
  "timeline": [
    {
      "iteration": 1,
      "exploitability": 0.875
    }
  ],
  "finalExploitability": 0.875,
  "decisions": [],
  "progress": 0.1,
  "done": false
}
```

O campo `timeline` alimenta o gráfico e a lista de passos.

O campo `finalExploitability` alimenta o indicador principal de exploitability.

O campo `source` alimenta o indicador de fonte.

O campo `progress` alimenta a barra de progresso.

O campo `done` determina quando o frontend fecha a conexão de streaming.

O campo `decisions` alimenta a seção de estratégia aprendida.

## Fluxo completo

1. O usuário abre o frontend em `http://127.0.0.1:5173`.
2. O Vite serve a aplicação React e encaminha chamadas `/api` para o backend.
3. O React inicia uma simulação padrão e consulta a disponibilidade do modo paper.
4. O backend monta um `SimulationConfig` com os parâmetros recebidos.
5. Dependendo do modo, a API chama `stream_kuhn()` ou `stream_paper_mocfr()`.
6. O backend envia snapshots por Server-Sent Events.
7. O frontend atualiza `data`, `status`, barra de progresso, gráfico, timeline e estratégia.
8. Quando recebe `done: true`, o frontend fecha a conexão SSE.

## Observações de manutenção

- O frontend está acoplado ao contrato JSON gerado pelo backend, principalmente aos campos `timeline`, `finalExploitability`, `decisions`, `progress` e `done`.
- O modo paper é opcional e depende de bibliotecas que podem não estar instaladas em todos os ambientes.
- O modo didático carrega um arquivo Python por caminho absoluto relativo ao repositório, então mover `NM-Method/Kuhn_Poker_CFR-style_MoCFR.py` exigiria ajustar `KUHN_ADAPTATION_PATH`.
- O treinamento didático usa estruturas globais (`regret` e `strategy_sum`) dentro da adaptação, mas elas são limpas no início das funções configuráveis.
- A comunicação em tempo real usa SSE, não WebSocket. Isso é suficiente aqui porque o fluxo principal é unidirecional: backend envia snapshots para o frontend.
