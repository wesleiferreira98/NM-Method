from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import ModuleType


ROOT_DIR = Path(__file__).resolve().parents[2]
KUHN_ADAPTATION_PATH = ROOT_DIR / "NM-Method" / "Kuhn_Poker_CFR-style_MoCFR.py"


@dataclass(frozen=True)
class SimulationConfig:
    iterations: int = 2000
    mu: float = 0.01
    interval: int = 200
    seed: int = 42


@lru_cache(maxsize=1)
def load_kuhn_adaptation() -> ModuleType:
    spec = importlib.util.spec_from_file_location("kuhn_poker_cfr_style_mocfr", KUHN_ADAPTATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar {KUHN_ADAPTATION_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def train_kuhn(config: SimulationConfig) -> dict:
    module = load_kuhn_adaptation()
    run_config = module.RunConfig(
        iterations=config.iterations,
        mu=config.mu,
        interval=config.interval,
        seed=config.seed,
        n_cards=3,
    )
    return module.run_structured(run_config)


def stream_kuhn(config: SimulationConfig):
    module = load_kuhn_adaptation()
    run_config = module.RunConfig(
        iterations=config.iterations,
        mu=config.mu,
        interval=config.interval,
        seed=config.seed,
        n_cards=3,
    )
    yield from module.iter_structured_snapshots(run_config)


def action_label(history: str, action_index: int) -> str:
    module = load_kuhn_adaptation()
    return module.ACTION_LABELS[history][action_index]
