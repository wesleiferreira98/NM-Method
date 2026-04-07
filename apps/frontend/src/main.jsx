import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const DEFAULT_PARAMS = {
  iterations: 2000,
  mu: 0.01,
  interval: 200,
  seed: 42,
  mode: "paper",
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

function formatExploitability(value, digits = 6) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "...";
  }

  if (value === 0) {
    return "0";
  }

  const absValue = Math.abs(value);

  if (absValue < 10 ** -digits) {
    return value.toExponential(2);
  }

  return value.toFixed(digits);
}

function modeLabel(mode) {
  return mode === "paper" ? "Paper fork" : "Didático";
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

function TooltipButton({ active, children, onClick, tooltip }) {
  return (
    <span className="tooltip-wrap">
      <button
        className={active ? "active" : ""}
        onClick={onClick}
        type="button"
      >
        {children}
      </button>
      <span className="metric-tooltip" role="tooltip">{tooltip}</span>
    </span>
  );
}

function getDecisionInsight(decision) {
  if (!decision) {
    return "Rode o treinamento e escolha uma carta para ver como interpretar uma decisão específica.";
  }

  const preferredAction = decision.checkCall >= decision.betRaise ? "Check/Call" : "Bet/Raise";
  const preferredPercent = formatPercent(Math.max(decision.checkCall, decision.betRaise));
  const context = historyLabels[decision.history] ?? decision.history;

  return `Com ${decision.card} para o Jogador ${decision.player} em "${context}", a política favorece ${preferredAction} em ${preferredPercent}. Isso não significa jogar sempre a mesma ação: em poker, misturar frequências ajuda a estratégia a ficar menos previsível.`;
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
      areaPath: "",
      comparisonPath: "",
      comparisonPlotPoints: [],
      maxExploitability: 0,
      path: "",
      plotPoints: [],
      width,
      height,
      padding
    };
  }

  const maxExploitability = Math.max(...allPoints.map((point) => point.exploitability), 0.001);
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const baselineY = height - padding.bottom;

  function toPlotPoints(series) {
    return series.map((point, index) => {
      const x =
        series.length === 1
          ? padding.left
          : padding.left + (index / (series.length - 1)) * plotWidth;
      const y = baselineY - (point.exploitability / maxExploitability) * plotHeight;
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
  const path = toPath(plotPoints);
  const comparisonPath = toPath(comparisonPlotPoints);
  const areaPath = path
    ? `${path} L ${plotPoints.at(-1).x.toFixed(2)} ${baselineY} L ${plotPoints[0].x.toFixed(2)} ${baselineY} Z`
    : "";

  return {
    areaPath,
    comparisonPath,
    comparisonPlotPoints,
    maxExploitability,
    path,
    plotPoints,
    width,
    height,
    padding
  };
}

function getComparisonDelta(data) {
  if (!data?.comparison) {
    return null;
  }

  return data.comparison.finalExploitability - data.finalExploitability;
}

function primaryMethodLabel(data) {
  return data?.comparison?.primaryLabel ?? "MoCFR";
}

function baselineMethodLabel(data) {
  return data?.comparison?.label ?? "CFR";
}

function comparisonWinner(data) {
  const delta = getComparisonDelta(data);

  if (delta === null) {
    return "...";
  }

  if (delta === 0) {
    return "Empate";
  }

  return delta > 0 ? primaryMethodLabel(data) : baselineMethodLabel(data);
}

function comparisonNote(data) {
  const delta = getComparisonDelta(data);

  if (delta === null) {
    return "Menor exploitability final vence.";
  }

  if (delta === 0) {
    return "Mesma exploitability final.";
  }

  return `Diferença: ${formatExploitability(Math.abs(delta))}.`;
}

function strategyApproachLabel(data, approach) {
  return approach === "comparison" ? baselineMethodLabel(data) : primaryMethodLabel(data);
}

function strategyDecisions(data, approach) {
  if (!data) {
    return [];
  }

  return approach === "comparison"
    ? data.comparison?.decisions ?? []
    : data.decisions ?? [];
}

function gridLines(chart) {
  return [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const y =
      chart.height -
      chart.padding.bottom -
      ratio * (chart.height - chart.padding.top - chart.padding.bottom);
    return {
      label: formatExploitability(chart.maxExploitability * ratio, 3),
      y
    };
  });
}

function Chart({ points, comparison }) {
  const comparisonPoints = comparison?.timeline ?? [];
  const chart = useMemo(() => getChartGeometry(points, comparisonPoints), [points, comparisonPoints]);
  const latestPoint = chart.plotPoints.at(-1);
  const lines = gridLines(chart);
  const primaryLabel = comparison?.primaryLabel ?? "MoCFR";

  return (
    <div className="chart-frame">
      <div className="chart-legend" aria-label="Séries do gráfico">
        <span><i className="legend-dot mocfr" />{primaryLabel}</span>
        {comparisonPoints.length ? <span><i className="legend-dot cfr" />{comparison.label}</span> : null}
      </div>
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
            <text x={Math.max(chart.padding.left + 8, latestPoint.x - 96)} y={chart.padding.top - 8}>
              Iter {latestPoint.iteration} · {formatExploitability(latestPoint.exploitability)}
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
  const [selectedApproach, setSelectedApproach] = useState("primary");
  const eventSourceRef = useRef(null);

  const selectedDecisions = useMemo(() => {
    return strategyDecisions(data, selectedApproach).filter(
      (decision) => decision.card === selectedCard
    );
  }, [data, selectedApproach, selectedCard]);

  const selectedDecisionsByPlayer = useMemo(() => {
    return [1, 2].map((player) => ({
      player,
      decisions: selectedDecisions.filter((decision) => decision.player === player),
    }));
  }, [selectedDecisions]);

  const latestStep = data?.timeline?.at(-1);
  const progress = data?.progress ?? (data ? 1 : 0);
  const isRunning = status === "loading" || status === "streaming";
  const selectedDecisionInsight = getDecisionInsight(selectedDecisions[0]);

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

  function stopSimulation() {
    closeStream();
    setStatus(data ? "ready" : "idle");
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
                : `Modo paper indisponível: ${paperStatus?.reason ?? "verificando dependências."}`
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

          <button
            className={isRunning ? "primary-action secondary" : "primary-action"}
            onClick={() => (isRunning ? stopSimulation() : runSimulation())}
            type="button"
          >
            {isRunning ? "Parar treinamento" : "Rodar treinamento"}
          </button>
          {error ? <p className="error">{error}</p> : null}
        </aside>

        <section className="monitor-panel">
          <div className="status-row">
            <MetricCard
              label={`${primaryMethodLabel(data)} final`}
              tooltip={`Exploitability final do ${primaryMethodLabel(data)}. Quanto menor, menos explorável é a política aprendida por esse método.`}
              value={formatExploitability(data?.finalExploitability)}
            />
            <MetricCard
              label={`${baselineMethodLabel(data)} final`}
              tooltip={`Exploitability final do ${baselineMethodLabel(data)}. Serve como base para comparar contra o MoCFR no mesmo treino.`}
              value={formatExploitability(data?.comparison?.finalExploitability)}
            />
            <MetricCard
              label="Vencedor"
              note={comparisonNote(data)}
              tooltip="Vence o método com menor exploitability final. A diferença indica quanto um terminou menos explorável que o outro."
              value={comparisonWinner(data)}
            />
            <MetricCard
              label="Fonte"
              tooltip="Implementação usada nesta simulação. Paper fork chama o código do paper; Didático usa a adaptação visual local."
              value={data?.source ? modeLabel(data.source) : modeLabel(params.mode)}
            />
            <MetricCard
              label="Status"
              tooltip="Estado atual da execução. Conectando aguarda o primeiro checkpoint; Ao vivo recebe checkpoints; Pronto indica fim ou parada."
              value={status === "loading" ? "Conectando" : status === "streaming" ? "Ao vivo" : status === "error" ? "Erro" : "Pronto"}
            />
          </div>

          <div className="progress-track" aria-label="Progresso do treinamento">
            <span style={{ width: formatPercent(progress) }} />
          </div>

          <div className="chart-block">
            <div>
              <h2>Convergência</h2>
              <p>
                A linha verde mostra {data?.comparison?.primaryLabel ?? "MoCFR"}. Quando disponível,
                a linha laranja mostra {data?.comparison?.label ?? "CFR"} com os mesmos parâmetros e
                sem momento negativo.
              </p>
            </div>
            <Chart points={data?.timeline ?? []} comparison={data?.comparison} />
          </div>
        </section>
      </section>

      <section className="learning-grid">
        <article className="learning-card">
          <span className="label">Exploitability</span>
          <h2>Quanto menor, menos explorável</h2>
          <p>
            Esse número estima quanto uma melhor resposta ainda conseguiria explorar a política
            aprendida. A curva ideal cai ao longo das iterações.
          </p>
        </article>
        <article className="learning-card">
          <span className="label">Momento negativo</span>
          <h2>Uma força de correção</h2>
          <p>
            O parâmetro μ puxa os arrependimentos atuais em direção a uma referência periódica.
            A comparação com CFR ajuda a ver se essa força acelerou a convergência neste treino.
          </p>
        </article>
        <article className="learning-card">
          <span className="label">Decisão selecionada</span>
          <h2>Como ler a política</h2>
          <p>{selectedDecisionInsight}</p>
        </article>
      </section>

      <section className="details-grid">
        <section className="timeline-panel">
          <h2>Passos do treinamento</h2>
          <ol>
            {(data?.timeline ?? []).map((point) => (
              <li key={point.iteration}>
                <span>Iteração {point.iteration}</span>
                <strong>{formatExploitability(point.exploitability)}</strong>
              </li>
            ))}
          </ol>
        </section>

        <section className="strategy-panel">
          <div className="strategy-header">
            <div className="strategy-title tooltip-wrap" tabIndex="0">
              <h2>Estratégia aprendida</h2>
              <p>Escolha uma abordagem e uma carta para ver a política atual por jogador.</p>
              <span className="metric-tooltip" role="tooltip">
                Mostra as probabilidades que a política treinada atribui para Check/Call e Bet/Raise em cada situação do Kuhn Poker.
              </span>
            </div>
            <div className="toggle-row">
              {["primary", "comparison"].map((approach) => (
                <TooltipButton
                  active={selectedApproach === approach}
                  key={approach}
                  onClick={() => setSelectedApproach(approach)}
                  tooltip={`Mostra as decisões aprendidas pela abordagem ${strategyApproachLabel(data, approach)}.`}
                >
                  {strategyApproachLabel(data, approach)}
                </TooltipButton>
              ))}
            </div>
          </div>

          <div className="card-picker" aria-label="Cartas do Kuhn Poker">
            {["J", "Q", "K"].map((card) => (
              <TooltipButton
                active={selectedCard === card}
                key={card}
                onClick={() => setSelectedCard(card)}
                tooltip={`Filtra as decisões quando a carta privada do jogador é ${card}.`}
              >
                {card}
              </TooltipButton>
            ))}
          </div>

          <p className="action-legend">
            <strong>Check/Call:</strong> passar quando não houve aposta ou pagar uma aposta.
            <strong> Bet/Raise:</strong> apostar ou aumentar a aposta.
          </p>

          <div className="decision-list">
            {selectedDecisionsByPlayer.map(({ player, decisions }) => (
              <section className="player-decisions" key={player}>
                <h3>Jogador {player} · {strategyApproachLabel(data, selectedApproach)}</h3>
                {decisions.map((decision) => (
                  <article className="decision" key={decision.key} tabIndex="0">
                    <div>
                      <h4>{historyLabels[decision.history] ?? decision.history}</h4>
                      <p>Ação recomendada: {decision.recommendedAction}</p>
                      <small className="metric-note">Abordagem: {strategyApproachLabel(data, selectedApproach)}</small>
                    </div>
                    <div className="bars">
                      <span
                        className="tooltip-wrap"
                        style={{ width: formatPercent(decision.checkCall) }}
                      >
                        Check/Call {formatPercent(decision.checkCall)}
                        <span className="metric-tooltip" role="tooltip">
                          Check significa passar sem apostar. Call significa pagar uma aposta. O percentual é a frequência escolhida por {strategyApproachLabel(data, selectedApproach)} nesta situação.
                        </span>
                      </span>
                      <span
                        className="tooltip-wrap"
                        style={{ width: formatPercent(decision.betRaise) }}
                      >
                        Bet/Raise {formatPercent(decision.betRaise)}
                        <span className="metric-tooltip" role="tooltip">
                          Bet significa apostar. Raise significa aumentar uma aposta. O percentual é a frequência escolhida por {strategyApproachLabel(data, selectedApproach)} nesta situação.
                        </span>
                      </span>
                    </div>
                    <span className="metric-tooltip" role="tooltip">
                      Carta {decision.card}, {historyLabels[decision.history] ?? decision.history}. A ação recomendada é a maior frequência da política aprendida, não uma regra fixa.
                    </span>
                  </article>
                ))}
              </section>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
