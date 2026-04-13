from __future__ import annotations

import json
import time

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from mcts_service import SimulationConfig, run_mcts_comparison, stream_mcts_comparison


app = FastAPI(title="Ancestor-Based MCTS API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/simulate")
def simulate(
    matches: int = Query(default=80, ge=2, le=500),
    simulations: int = Query(default=300, ge=10, le=5000),
    c: float = Query(default=1.35, ge=0.0, le=5.0),
    c_alpha_beta: float = Query(default=1.2, ge=0.0, le=5.0),
    seed: int = Query(default=42, ge=0, le=1_000_000),
    board_size: int = Query(default=5, ge=3, le=7),
    win_length: int = Query(default=4, ge=3, le=7),
) -> dict:
    config = SimulationConfig(
        matches=matches,
        simulations=simulations,
        c=c,
        c_alpha_beta=c_alpha_beta,
        seed=seed,
        board_size=board_size,
        win_length=win_length,
    )
    return run_mcts_comparison(config)


@app.get("/api/simulate/stream")
def simulate_stream(
    matches: int = Query(default=80, ge=2, le=500),
    simulations: int = Query(default=300, ge=10, le=5000),
    c: float = Query(default=1.35, ge=0.0, le=5.0),
    c_alpha_beta: float = Query(default=1.2, ge=0.0, le=5.0),
    seed: int = Query(default=42, ge=0, le=1_000_000),
    board_size: int = Query(default=5, ge=3, le=7),
    win_length: int = Query(default=4, ge=3, le=7),
    delay_ms: int = Query(default=120, ge=0, le=2000),
):
    config = SimulationConfig(
        matches=matches,
        simulations=simulations,
        c=c,
        c_alpha_beta=c_alpha_beta,
        seed=seed,
        board_size=board_size,
        win_length=win_length,
    )

    def event_generator():
        try:
            for snapshot in stream_mcts_comparison(config):
                yield f"data: {json.dumps(snapshot)}\n\n"
                if delay_ms > 0 and not snapshot.get("done", False):
                    time.sleep(delay_ms / 1000)
        except RuntimeError as error:
            payload = {"error": str(error), "done": True}
            yield f"event: stream-error\ndata: {json.dumps(payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
