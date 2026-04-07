from __future__ import annotations

import json
import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from kuhn_service import SimulationConfig, stream_kuhn, train_kuhn
from paper_bridge import check_paper_availability, run_paper_mocfr, stream_paper_mocfr


app = FastAPI(title="NM Method Poker API", version="0.1.0")

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


@app.get("/api/paper/status")
def paper_status() -> dict:
    availability = check_paper_availability()
    return {
        "available": availability.available,
        "reason": availability.reason,
    }


@app.get("/api/simulate")
def simulate(
    iterations: int = Query(default=2000, ge=50, le=50000),
    mu: float = Query(default=0.01, ge=0.0, le=1.0),
    interval: int = Query(default=200, ge=1, le=10000),
    seed: int = Query(default=42, ge=0, le=1_000_000),
    mode: str = Query(default="educational", pattern="^(educational|paper)$"),
) -> dict:
    config = SimulationConfig(
        iterations=iterations,
        mu=mu,
        interval=interval,
        seed=seed,
    )

    if mode == "paper":
        try:
            return run_paper_mocfr(config)
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    result = train_kuhn(config)
    result["source"] = "educational"
    return result


@app.get("/api/simulate/stream")
def simulate_stream(
    iterations: int = Query(default=2000, ge=50, le=50000),
    mu: float = Query(default=0.01, ge=0.0, le=1.0),
    interval: int = Query(default=200, ge=1, le=10000),
    seed: int = Query(default=42, ge=0, le=1_000_000),
    mode: str = Query(default="educational", pattern="^(educational|paper)$"),
    delay_ms: int = Query(default=120, ge=0, le=2000),
):
    config = SimulationConfig(
        iterations=iterations,
        mu=mu,
        interval=interval,
        seed=seed,
    )

    def event_generator():
        try:
            stream = stream_paper_mocfr(config) if mode == "paper" else stream_kuhn(config)
            for snapshot in stream:
                yield f"data: {json.dumps(snapshot)}\n\n"
                if delay_ms > 0 and not snapshot.get("done", False):
                    time.sleep(delay_ms / 1000)
        except RuntimeError as error:
            payload = {"error": str(error), "done": True}
            yield f"event: stream-error\ndata: {json.dumps(payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
