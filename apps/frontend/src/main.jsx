import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const DEFAULT_PARAMS = {
  matches: 80,
  simulations: 300,
  c: 1.35,
  cAlphaBeta: 1.2,
  seed: 42,
  boardSize: 5,
  winLength: 4,
  delayMs: 120
};

function formatDecimal(value, digits = 3) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "...";
  }

  return Number(value).toFixed(digits);
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "...";
  }

  return `${Math.round(value * 100)}%`;
}

function methodWinner(data) {
  if (!data) {
    return "...";
  }

  if (data.finalScore === data.comparison?.finalScore) {
    return "Empate";
  }

  return data.finalScore > data.comparison?.finalScore ? "UCTαβ" : "UCT";
}

function scoreNote(data) {
  if (!data) {
    return "Score soma vitória como 1 e empate como 0.5.";
  }

  const delta = Math.abs(data.finalScore - data.comparison.finalScore);
  return `Diferença: ${formatDecimal(delta)}.`;
}

function MetricCard({ label, note, tooltip, value }) {
  return (
    <div className="metric-card" tabIndex="0">
      <span className="label">{label}</span>
      <strong>{value}</strong>
      {note ? <small className="metric-note">{note}</small> : null}
      <span className="metric-tooltip" role="tooltip">{tooltip}</span>
    </div>
  );
}

function getChartGeometry(points, comparisonPoints = []) {
  const width = 720;
  const height = 260;
  const padding = {
    top: 28,
    right: 34,
    bottom: 42,
    left: 58
  };
  const allPoints = [...points, ...comparisonPoints];

  if (!allPoints.length) {
    return {
      comparisonPath: "",
      comparisonPlotPoints: [],
      path: "",
      plotPoints: [],
      width,
      height,
      padding
    };
  }

  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const baselineY = height - padding.bottom;

  function toPlotPoints(series) {
    return series.map((point, index) => {
      const x =
        series.length === 1
          ? padding.left
          : padding.left + (index / (series.length - 1)) * plotWidth;
      const y = baselineY - point.score * plotHeight;
      return {
        ...point,
        x,
        y
      };
    });
  }

  function toPath(series) {
    return series
      .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
      .join(" ");
  }

  const plotPoints = toPlotPoints(points);
  const comparisonPlotPoints = toPlotPoints(comparisonPoints);

  return {
    comparisonPath: toPath(comparisonPlotPoints),
    comparisonPlotPoints,
    path: toPath(plotPoints),
    plotPoints,
    width,
    height,
    padding
  };
}

function gridLines(chart) {
  return [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const y =
      chart.height -
      chart.padding.bottom -
      ratio * (chart.height - chart.padding.top - chart.padding.bottom);
    return {
      label: formatDecimal(ratio, 2),
      y
    };
  });
}

function Chart({ points, comparison }) {
  const comparisonPoints = comparison?.timeline ?? [];
  const chart = useMemo(() => getChartGeometry(points, comparisonPoints), [points, comparisonPoints]);
  const latestPoint = chart.plotPoints.at(-1);
  const lines = gridLines(chart);

  return (
    <div className="chart-frame">
      <div className="chart-legend" aria-label="Séries do gráfico">
        <span><i className="legend-dot alphabeta" />UCTαβ</span>
        <span><i className="legend-dot uct" />UCT</span>
      </div>
      <svg viewBox={`0 0 ${chart.width} ${chart.height}`} role="img" aria-label="Score acumulado por partida">
        <rect className="chart-surface" x="0" y="0" width={chart.width} height={chart.height} rx="8" />
        {lines.map((line) => (
          <g className="grid-line" key={line.y}>
            <line x1={chart.padding.left} x2={chart.width - chart.padding.right} y1={line.y} y2={line.y} />
            <text x="16" y={line.y + 4}>{line.label}</text>
          </g>
        ))}
        <line
          className="axis-line"
          x1={chart.padding.left}
          x2={chart.width - chart.padding.right}
          y1={chart.height - chart.padding.bottom}
          y2={chart.height - chart.padding.bottom}
        />
        <line
          className="axis-line"
          x1={chart.padding.left}
          x2={chart.padding.left}
          y1={chart.padding.top}
          y2={chart.height - chart.padding.bottom}
        />
        {chart.comparisonPath ? <path className="chart-line comparison" d={chart.comparisonPath} /> : null}
        {chart.path ? <path className="chart-line" d={chart.path} /> : null}
        {chart.comparisonPlotPoints.map((point, index) => (
          <circle
            className="chart-dot comparison"
            cx={point.x}
            cy={point.y}
            key={`comparison-${point.iteration}-${index}`}
            r={2.5}
          />
        ))}
        {chart.plotPoints.map((point, index) => (
          <circle
            className={index === chart.plotPoints.length - 1 ? "chart-dot current" : "chart-dot"}
            cx={point.x}
            cy={point.y}
            key={`${point.iteration}-${index}`}
            r={index === chart.plotPoints.length - 1 ? 5 : 3}
          />
        ))}
        {latestPoint ? (
          <g className="latest-marker">
            <line
              x1={latestPoint.x}
              x2={latestPoint.x}
              y1={chart.padding.top}
              y2={chart.height - chart.padding.bottom}
            />
            <text x={Math.max(chart.padding.left + 8, latestPoint.x - 98)} y={chart.padding.top - 8}>
              Partida {latestPoint.iteration} · {formatDecimal(latestPoint.score)}
            </text>
          </g>
        ) : null}
        <text className="axis-label" x={chart.width / 2 - 36} y={chart.height - 10}>partidas</text>
        <text className="axis-label y-label" x="-142" y="18" transform="rotate(-90)">score</text>
      </svg>
    </div>
  );
}

function Board({ match, size }) {
  const board = match?.board ?? [];

  return (
    <div className="board-wrap">
      <div className="board" style={{ gridTemplateColumns: `repeat(${size}, minmax(0, 1fr))` }}>
        {Array.from({ length: size * size }).map((_, index) => (
          <span className={board[index] === "." ? "empty" : ""} key={index}>
            {board[index] === "." || !board[index] ? "" : board[index]}
          </span>
        ))}
      </div>
      <p>
        Última partida: {match ? `${match.winnerMethod} (${match.winner})` : "aguardando simulação"}.
      </p>
    </div>
  );
}

function MoveList({ moves }) {
  return (
    <ol className="move-list">
      {(moves ?? []).slice(-10).map((move) => (
        <li key={move.move}>
          <span>{move.move}. {move.method}</span>
          <strong>{move.player} em {move.row + 1},{move.col + 1}</strong>
        </li>
      ))}
    </ol>
  );
}

function App() {
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const eventSourceRef = useRef(null);

  const latestStep = data?.timeline?.at(-1);
  const progress = data?.progress ?? (data ? 1 : 0);
  const isRunning = status === "loading" || status === "streaming";

  function closeStream() {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }

  function buildQuery(nextParams) {
    return new URLSearchParams({
      matches: String(nextParams.matches),
      simulations: String(nextParams.simulations),
      c: String(nextParams.c),
      c_alpha_beta: String(nextParams.cAlphaBeta),
      seed: String(nextParams.seed),
      board_size: String(nextParams.boardSize),
      win_length: String(nextParams.winLength),
      delay_ms: String(nextParams.delayMs)
    });
  }

  function runSimulationStream(nextParams) {
    const query = buildQuery(nextParams);
    const source = new EventSource(`/api/simulate/stream?${query.toString()}`);
    eventSourceRef.current = source;

    source.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      setData(payload);
      setStatus(payload.done ? "ready" : "streaming");
      if (payload.done) {
        source.close();
        eventSourceRef.current = null;
      }
    };

    source.addEventListener("stream-error", (event) => {
      try {
        const payload = JSON.parse(event.data);
        setError(payload.error ?? "A conexão em tempo real foi interrompida.");
      } catch {
        setError("A conexão em tempo real foi interrompida.");
      }
      source.close();
      eventSourceRef.current = null;
      setData(null);
      setStatus("error");
    });

    source.onerror = () => {
      if (eventSourceRef.current !== source) {
        return;
      }
      source.close();
      eventSourceRef.current = null;
      setData(null);
      setStatus("error");
      setError("A conexão em tempo real foi interrompida.");
    };
  }

  function runSimulation(nextParams = params) {
    closeStream();
    setStatus("loading");
    setError("");
    setData(null);
    runSimulationStream(nextParams);
  }

  function stopSimulation() {
    closeStream();
    setStatus(data ? "ready" : "idle");
  }

  useEffect(() => {
    runSimulation(DEFAULT_PARAMS);
    return closeStream;
  }, []);

  function updateParam(name, value) {
    const numericValue = name === "c" || name === "cAlphaBeta" ? Number(value) : Number.parseInt(value, 10);
    setParams((current) => ({
      ...current,
      [name]: numericValue
    }));
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Ancestor-Based α-β Bounds</p>
          <h1>MCTS com UCTαβ</h1>
          <p>
            Compare partidas entre UCTαβ e UCT em Mini Gomoku, acompanhando o score
            acumulado e a última busca feita pelo agente.
          </p>
        </div>
        <div className="hero-metrics">
          <span>Partida</span>
          <strong>{latestStep ? latestStep.iteration : 0}</strong>
          <small>de {params.matches}</small>
        </div>
      </section>

      <section className="simulation-grid">
        <aside className="control-panel">
          <h2>Configuração</h2>
          <p className="helper">
            O ambiente alterna quem começa para reduzir viés de primeiro jogador.
          </p>

          <label>
            Partidas
            <input
              min="2"
              max="500"
              onChange={(event) => updateParam("matches", event.target.value)}
              type="number"
              value={params.matches}
            />
          </label>
          <label>
            Simulações por lance
            <input
              min="10"
              max="5000"
              onChange={(event) => updateParam("simulations", event.target.value)}
              type="number"
              value={params.simulations}
            />
          </label>
          <label>
            Constante UCT C
            <input
              max="5"
              min="0"
              onChange={(event) => updateParam("c", event.target.value)}
              step="0.05"
              type="number"
              value={params.c}
            />
          </label>
          <label>
            Constante Cαβ
            <input
              max="5"
              min="0"
              onChange={(event) => updateParam("cAlphaBeta", event.target.value)}
              step="0.05"
              type="number"
              value={params.cAlphaBeta}
            />
          </label>
          <label>
            Tamanho do tabuleiro
            <input
              min="3"
              max="7"
              onChange={(event) => updateParam("boardSize", event.target.value)}
              type="number"
              value={params.boardSize}
            />
          </label>
          <label>
            Linha para vencer
            <input
              min="3"
              max="7"
              onChange={(event) => updateParam("winLength", event.target.value)}
              type="number"
              value={params.winLength}
            />
          </label>
          <label>
            Semente
            <input
              min="0"
              max="1000000"
              onChange={(event) => updateParam("seed", event.target.value)}
              type="number"
              value={params.seed}
            />
          </label>

          <label className="speed-control">
            Velocidade dos checkpoints
            <input
              min="0"
              max="1200"
              onChange={(event) => updateParam("delayMs", event.target.value)}
              step="40"
              type="range"
              value={params.delayMs}
            />
            <span>{params.delayMs === 0 ? "instantâneo" : `${params.delayMs} ms por checkpoint`}</span>
          </label>

          <button
            className={isRunning ? "primary-action secondary" : "primary-action"}
            onClick={() => (isRunning ? stopSimulation() : runSimulation())}
            type="button"
          >
            {isRunning ? "Parar comparação" : "Rodar comparação"}
          </button>
          {error ? <p className="error">{error}</p> : null}
        </aside>

        <section className="monitor-panel">
          <div className="status-row">
            <MetricCard
              label="Score UCTαβ"
              tooltip="Score médio do UCTαβ: vitória vale 1, empate vale 0.5 e derrota vale 0."
              value={formatDecimal(data?.finalScore)}
            />
            <MetricCard
              label="Score UCT"
              tooltip="Score médio do UCT padrão no mesmo conjunto de partidas."
              value={formatDecimal(data?.comparison?.finalScore)}
            />
            <MetricCard
              label="Vencedor"
              note={scoreNote(data)}
              tooltip="Vence o método com maior score acumulado."
              value={methodWinner(data)}
            />
            <MetricCard
              label="Vitórias UCTαβ"
              tooltip="Percentual de partidas vencidas por UCTαβ. Empates aparecem no painel do tabuleiro."
              value={formatPercent(latestStep?.winRate)}
            />
            <MetricCard
              label="Status"
              tooltip="Estado atual da execução. Conectando aguarda o primeiro checkpoint; Ao vivo recebe checkpoints; Pronto indica fim ou parada."
              value={status === "loading" ? "Conectando" : status === "streaming" ? "Ao vivo" : status === "error" ? "Erro" : "Pronto"}
            />
          </div>

          <div className="progress-track" aria-label="Progresso da comparação">
            <span style={{ width: formatPercent(progress) }} />
          </div>

          <div className="chart-block">
            <div>
              <h2>Score acumulado</h2>
              <p>
                A linha verde mostra UCTαβ. A linha laranja mostra UCT no mesmo
                orçamento de simulações por lance.
              </p>
            </div>
            <Chart points={data?.timeline ?? []} comparison={data?.comparison} />
          </div>
        </section>
      </section>

      <section className="learning-grid">
        <article className="learning-card">
          <span className="label">UCT</span>
          <h2>Busca local por confiança</h2>
          <p>
            Tempo por lance: O(S · d · b). Espaço: O(T). A seleção varre os filhos
            do nó atual usando média e bônus de exploração.
          </p>
        </article>
        <article className="learning-card">
          <span className="label">UCTαβ</span>
          <h2>Ancestrais entram na seleção</h2>
          <p>
            Tempo por lance: O(S · d · b). Espaço: O(T) + O(1) por simulação.
            O ganho ou perda vem do custo constante dos limites α e β.
          </p>
        </article>
        <article className="learning-card">
          <span className="label">Ambiente</span>
          <h2>Mini Gomoku determinístico</h2>
          <p>
            Cada partida usa tabuleiro local, recompensa de soma zero e alternância
            de primeiro jogador entre os métodos.
          </p>
        </article>
      </section>

      <section className="details-grid">
        <section className="timeline-panel">
          <h2>Checkpoints</h2>
          <ol>
            {(data?.timeline ?? []).map((point) => (
              <li key={point.iteration}>
                <span>Partida {point.iteration}</span>
                <strong>{formatDecimal(point.score)}</strong>
              </li>
            ))}
          </ol>
        </section>

        <section className="strategy-panel">
          <div className="strategy-header">
            <div className="strategy-title tooltip-wrap" tabIndex="0">
              <h2>Última partida</h2>
              <p>Veja o tabuleiro final e os últimos lances da comparação.</p>
              <span className="metric-tooltip" role="tooltip">
                X e O alternam conforme o jogador da partida; o método associado muda porque UCTαβ e UCT alternam quem começa.
              </span>
            </div>
          </div>

          <div className="match-grid">
            <Board match={data?.lastMatch} size={params.boardSize} />
            <div>
              <p className="action-legend">
                <strong>Score:</strong> {formatDecimal(data?.finalScore)} para UCTαβ.
                <strong> Empates:</strong> {latestStep ? latestStep.draws : 0}.
              </p>
              <MoveList moves={data?.lastMatch?.moves} />
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
