from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from kuhn_service import SimulationConfig, action_label


ROOT_DIR = Path(__file__).resolve().parents[2]
PAPER_CODE_DIR = ROOT_DIR / "NM-Method"
CHECKPOINTS = 24
OPEN_SPIEL_CARD_LABELS = {"0": "J", "1": "Q", "2": "K"}
OPEN_SPIEL_HISTORY_LABELS = {
    "": "inicio",
    "p": "c",
    "b": "b",
    "pb": "cb",
}


@dataclass(frozen=True)
class PaperAvailability:
    available: bool
    reason: str | None = None


def check_paper_availability() -> PaperAvailability:
    if not PAPER_CODE_DIR.exists():
        return PaperAvailability(False, f"Diretorio nao encontrado: {PAPER_CODE_DIR}")

    try:
        import attr  # noqa: F401
        import numpy  # noqa: F401
        import pyspiel  # noqa: F401
        from open_spiel.python.algorithms import exploitability  # noqa: F401
    except ImportError as error:
        return PaperAvailability(False, f"Dependencia ausente: {error.name}")

    return PaperAvailability(True)


def _load_paper_modules():
    if str(PAPER_CODE_DIR) not in sys.path:
        sys.path.insert(0, str(PAPER_CODE_DIR))

    import MoCFR
    import pyspiel
    from open_spiel.python.algorithms import exploitability

    return MoCFR, pyspiel, exploitability


def _policy_probability(policy, key: str, action: int) -> float:
    state_policy = policy.policy_for_key(key)
    return float(state_policy[action])


def _extract_kuhn_decisions(policy) -> list[dict]:
    decisions = []

    for key in sorted(policy.state_lookup.keys()):
        card_key = key[0]
        history = key[1:]
        if card_key not in OPEN_SPIEL_CARD_LABELS:
            continue

        try:
            check_call = _policy_probability(policy, key, 0)
            bet_raise = _policy_probability(policy, key, 1)
        except KeyError:
            continue

        player = 1 if len(history) % 2 == 0 else 2
        normalized_history = OPEN_SPIEL_HISTORY_LABELS.get(history, history)
        best_action_index = 0 if check_call >= bet_raise else 1
        decisions.append(
            {
                "key": key,
                "player": player,
                "card": OPEN_SPIEL_CARD_LABELS[card_key],
                "history": normalized_history,
                "checkCall": round(check_call, 4),
                "betRaise": round(bet_raise, 4),
                "recommendedAction": action_label(
                    "" if normalized_history == "inicio" else normalized_history,
                    best_action_index,
                ),
            }
        )

    return decisions


def run_paper_mocfr(config: SimulationConfig) -> dict:
    availability = check_paper_availability()
    if not availability.available:
        raise RuntimeError(availability.reason or "Codigo do paper indisponivel.")

    MoCFR, pyspiel, exploitability = _load_paper_modules()
    game = pyspiel.load_game("kuhn_poker")
    solver = MoCFR.CFRPlusSolver(game, itv=config.interval, mu=config.mu)
    checkpoint_every = max(1, config.iterations // CHECKPOINTS)
    timeline = []

    for iteration in range(1, config.iterations + 1):
        solver.evaluate_and_update_policy()
        if iteration == 1 or iteration % checkpoint_every == 0 or iteration == config.iterations:
            conv = exploitability.nash_conv(game, solver.current_policy())
            timeline.append(
                {
                    "iteration": iteration,
                    "exploitability": round(float(conv), 6),
                }
            )

    current_policy = solver.current_policy()

    return {
        "game": "Kuhn Poker",
        "method": "MoCFR from paper fork",
        "source": "paper",
        "config": {
            "iterations": config.iterations,
            "mu": config.mu,
            "interval": config.interval,
            "seed": config.seed,
        },
        "timeline": timeline,
        "finalExploitability": timeline[-1]["exploitability"],
        "decisions": _extract_kuhn_decisions(current_policy),
        "explanation": {
            "baseline": "Este modo chama o solver MoCFR.CFRPlusSolver do fork do paper.",
            "negativeMomentum": "O termo de momento negativo e aplicado dentro de NM-Method/MoCFR.py.",
            "separation": "A ponte fica em apps/backend/paper_bridge.py e nao altera os arquivos originais de pesquisa.",
        },
    }


def stream_paper_mocfr(config: SimulationConfig):
    availability = check_paper_availability()
    if not availability.available:
        raise RuntimeError(availability.reason or "Codigo do paper indisponivel.")

    MoCFR, pyspiel, exploitability = _load_paper_modules()
    game = pyspiel.load_game("kuhn_poker")
    solver = MoCFR.CFRPlusSolver(game, itv=config.interval, mu=config.mu)
    checkpoint_every = max(1, config.iterations // CHECKPOINTS)
    timeline = []

    for iteration in range(1, config.iterations + 1):
        solver.evaluate_and_update_policy()
        if iteration == 1 or iteration % checkpoint_every == 0 or iteration == config.iterations:
            current_policy = solver.current_policy()
            conv = exploitability.nash_conv(game, current_policy)
            exploitability_value = round(float(conv), 6)
            timeline.append(
                {
                    "iteration": iteration,
                    "exploitability": exploitability_value,
                }
            )
            yield {
                "game": "Kuhn Poker",
                "method": "MoCFR from paper fork",
                "source": "paper",
                "config": {
                    "iterations": config.iterations,
                    "mu": config.mu,
                    "interval": config.interval,
                    "seed": config.seed,
                },
                "timeline": timeline[:],
                "finalExploitability": exploitability_value,
                "decisions": _extract_kuhn_decisions(current_policy),
                "progress": round(iteration / config.iterations, 4),
                "currentIteration": iteration,
                "done": iteration == config.iterations,
                "explanation": {
                    "baseline": "Este modo chama o solver MoCFR.CFRPlusSolver do fork do paper.",
                    "negativeMomentum": "O termo de momento negativo e aplicado dentro de NM-Method/MoCFR.py.",
                    "separation": "A ponte fica em apps/backend/paper_bridge.py e nao altera os arquivos originais de pesquisa.",
                },
            }
