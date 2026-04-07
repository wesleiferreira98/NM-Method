import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const DEFAULT_PARAMS = {
  iterations: 2000,
  mu: 0.01,
  interval: 200,
  seed: 42,
  mode: "educational",
  delayMs: 120
};

const historyLabels = {
  inicio: "Início",
  c: "Check",
  b: "Bet",
  cb: "Check, Bet"
};

function formatPercent(value) {
  return `${Math.round(value * 100)}%`;
}

function modeLabel(mode) {
  return mode === "paper" ? "Paper fork" : "Didático";
}

function getChartGeometry(points) {
  const width = 720;
  const height = 260;
  const padding = {
    top: 28,
    right: 34,
    bottom: 42,
    left: 58
  };

  if (!points.length) {
    return {
      areaPath: "",
      maxExploitability: 0,
      path: "",
      plotPoints: [],
      width,
      height,
      padding
    };
  }

  const maxExploitability = Math.max(...points.map((point) => point.exploitability), 0.001);
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const baselineY = height - padding.bottom;

  const plotPoints = points.map((point, index) => {
    const x =
      points.length === 1
        ? padding.left
        : padding.left + (index / (points.length - 1)) * plotWidth;
    const y = baselineY - (point.exploitability / maxExploitability) * plotHeight;
    return {
      ...point,
      x,
      y
    };
  });

  const path = plotPoints
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(" ");

  const areaPath = `${path} L ${plotPoints.at(-1).x.toFixed(2)} ${baselineY} L ${plotPoints[0].x.toFixed(2)} ${baselineY} Z`;

  return {
    areaPath,
    maxExploitability,
    path,
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
      label: (chart.maxExploitability * ratio).toFixed(3),
      y
    };
  });
}

function Chart({ points }) {
  const chart = useMemo(() => getChartGeometry(points), [points]);
  const latestPoint = chart.plotPoints.at(-1);
  const lines = gridLines(chart);

  return (
    <div className="chart-frame">
      <svg viewBox={`0 0 ${chart.width} ${chart.height}`} role="img" aria-label="Curva de exploitability">
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
        {chart.areaPath ? <path className="chart-area" d={chart.areaPath} /> : null}
        {chart.path ? <path className="chart-line" d={chart.path} /> : null}
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
            <text x={Math.max(chart.padding.left + 8, latestPoint.x - 96)} y={chart.padding.top - 8}>
              Iter {latestPoint.iteration} · {latestPoint.exploitability.toFixed(6)}
            </text>
          </g>
        ) : null}
        <text className="axis-label" x={chart.width / 2 - 40} y={chart.height - 10}>iterações</text>
        <text className="axis-label y-label" x="-158" y="18" transform="rotate(-90)">exploitability</text>
      </svg>
    </div>
  );
}
function App() {
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [paperStatus, setPaperStatus] = useState(null);
  const [selectedCard, setSelectedCard] = useState("K");
  const [selectedPlayer, setSelectedPlayer] = useState(1);
  const eventSourceRef = useRef(null);

  const selectedDecisions = useMemo(() => {
    if (!data) {
      return [];
    }

    return data.decisions.filter(
      (decision) => decision.card === selectedCard && decision.player === selectedPlayer
    );
  }, [data, selectedCard, selectedPlayer]);

  const latestStep = data?.timeline?.at(-1);
  const progress = data?.progress ?? (data ? 1 : 0);

  function closeStream() {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }

  function buildQuery(nextParams) {
    return new URLSearchParams({
      iterations: String(nextParams.iterations),
      mu: String(nextParams.mu),
      interval: String(nextParams.interval),
      seed: String(nextParams.seed),
      mode: nextParams.mode,
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

  async function runSimulation(nextParams = params) {
    closeStream();
    setStatus("loading");
    setError("");
    setData(null);
    runSimulationStream(nextParams);
  }

  useEffect(() => {
    runSimulation(DEFAULT_PARAMS);
    fetch("/api/paper/status")
      .then((response) => response.json())
      .then(setPaperStatus)
      .catch(() => setPaperStatus({ available: false, reason: "Status indisponivel" }));

    return closeStream;
  }, []);

  function updateParam(name, value) {
    const nextParams = {
      ...params,
      [name]: name === "mu" ? Number(value) : Number.parseInt(value, 10)
    };
    setParams(nextParams);
  }

  function updateMode(mode) {
    const nextParams = {
      ...params,
      mode
    };
    setParams(nextParams);
    runSimulation(nextParams);
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Negative Momentum Method</p>
          <h1>Kuhn Poker em tempo real</h1>
          <p>
            Veja o treinamento avançar por checkpoints, acompanhe a exploitability
            cair e inspecione a estratégia aprendida por carta e jogador.
          </p>
        </div>
        <div className="hero-metrics">
          <span>Iteração</span>
          <strong>{latestStep ? latestStep.iteration : 0}</strong>
          <small>de {params.iterations}</small>
        </div>
      </section>

      <section className="simulation-grid">
        <aside className="control-panel">
          <h2>Configuração</h2>
          <div className="mode-options" aria-label="Modo da simulação">
            <button
              className={params.mode === "educational" ? "active" : ""}
              onClick={() => updateMode("educational")}
              type="button"
            >
              Didático
            </button>
            <button
              className={params.mode === "paper" ? "active" : ""}
              onClick={() => updateMode("paper")}
              type="button"
            >
              Paper fork
            </button>
          </div>
          <p className="helper">
            {params.mode === "paper"
              ? paperStatus?.available
                ? "Usando NM-Method/MoCFR.py com streaming de checkpoints."
                : `Modo paper indisponivel: ${paperStatus?.reason ?? "verificando dependencias."}`
              : "Usando Kuhn_Poker_CFR-style_MoCFR.py com streaming de checkpoints."}
          </p>

          <label>
            Iterações
            <input
              min="50"
              max="50000"
              onChange={(event) => updateParam("iterations", event.target.value)}
              type="number"
              value={params.iterations}
            />
          </label>
          <label>
            Momento negativo
            <input
              max="1"
              min="0"
              onChange={(event) => updateParam("mu", event.target.value)}
              step="0.005"
              type="number"
              value={params.mu}
            />
          </label>
          <label>
            Intervalo de referência
            <input
              min="1"
              max="10000"
              onChange={(event) => updateParam("interval", event.target.value)}
              type="number"
              value={params.interval}
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

          <button className="primary-action" onClick={() => runSimulation()} type="button">
            {status === "loading" || status === "streaming" ? "Treinando..." : "Rodar treinamento"}
          </button>
          {error ? <p className="error">{error}</p> : null}
        </aside>

        <section className="monitor-panel">
          <div className="status-row">
            <div>
              <span className="label">Exploitability</span>
              <strong>{data ? data.finalExploitability.toFixed(6) : "..."}</strong>
            </div>
            <div>
              <span className="label">Fonte</span>
              <strong>{data?.source ? modeLabel(data.source) : modeLabel(params.mode)}</strong>
            </div>
            <div>
              <span className="label">Status</span>
              <strong>{status === "streaming" ? "Ao vivo" : status === "error" ? "Erro" : "Pronto"}</strong>
            </div>
          </div>

          <div className="progress-track" aria-label="Progresso do treinamento">
            <span style={{ width: formatPercent(progress) }} />
          </div>

          <div className="chart-block">
            <div>
              <h2>Convergência</h2>
              <p>Cada ponto representa um checkpoint emitido pelo backend.</p>
            </div>
            <Chart points={data?.timeline ?? []} />
          </div>
        </section>
      </section>

      <section className="details-grid">
        <section className="timeline-panel">
          <h2>Passos do treinamento</h2>
          <ol>
            {(data?.timeline ?? []).map((point) => (
              <li key={point.iteration}>
                <span>Iteração {point.iteration}</span>
                <strong>{point.exploitability.toFixed(6)}</strong>
              </li>
            ))}
          </ol>
        </section>

        <section className="strategy-panel">
          <div className="strategy-header">
            <div>
              <h2>Estratégia aprendida</h2>
              <p>Escolha uma carta e um jogador para ver a política atual.</p>
            </div>
            <div className="toggle-row">
              {[1, 2].map((player) => (
                <button
                  className={selectedPlayer === player ? "active" : ""}
                  key={player}
                  onClick={() => setSelectedPlayer(player)}
                  type="button"
                >
                  Jogador {player}
                </button>
              ))}
            </div>
          </div>

          <div className="card-picker" aria-label="Cartas do Kuhn Poker">
            {["J", "Q", "K"].map((card) => (
              <button
                className={selectedCard === card ? "active" : ""}
                key={card}
                onClick={() => setSelectedCard(card)}
                type="button"
              >
                {card}
              </button>
            ))}
          </div>

          <div className="decision-list">
            {selectedDecisions.map((decision) => (
              <article className="decision" key={decision.key}>
                <div>
                  <h3>{historyLabels[decision.history] ?? decision.history}</h3>
                  <p>Ação recomendada: {decision.recommendedAction}</p>
                </div>
                <div className="bars">
                  <span style={{ width: formatPercent(decision.checkCall) }}>
                    Check/Call {formatPercent(decision.checkCall)}
                  </span>
                  <span style={{ width: formatPercent(decision.betRaise) }}>
                    Bet/Raise {formatPercent(decision.betRaise)}
                  </span>
                </div>
              </article>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
