"""FastAPI server for Beneath the Org Chart.

Serves a single static SPA at "/" plus a small JSON API:

  GET  /api/graph                 -> the full pre-built NIL graph
  GET  /api/graph/by-edge/{kind}  -> filtered to one NIL dimension
  POST /api/lookup                -> situation in, structured read out
  POST /api/briefing              -> external artifact in, structured briefing out

The graph itself is generated offline by `python -m extraction.run` and shipped
as app/data/graph.json. The Atlas surface never calls an LLM at runtime; the
Lookup and Briefing surfaces call Claude when ANTHROPIC_API_KEY is set, and
fall back to a deterministic stub otherwise.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .briefing import briefing as run_briefing
from .lookup import lookup as run_lookup

APP_DIR = Path(__file__).resolve().parent
GRAPH_PATH = APP_DIR / "data" / "graph.json"

app = FastAPI(title="Beneath the Org Chart")


class LookupRequest(BaseModel):
    situation: str = Field(min_length=1, max_length=4000)


class BriefingRequest(BaseModel):
    artifact: str = Field(min_length=1, max_length=16000)


def _load_graph() -> dict:
    if not GRAPH_PATH.exists():
        # Empty graph until extraction has run for the first time.
        return {"nodes": [], "edges": [], "generated_at": None, "source": "empty"}
    return json.loads(GRAPH_PATH.read_text())


@app.get("/api/graph")
def get_graph() -> JSONResponse:
    return JSONResponse(_load_graph())


@app.get("/api/graph/by-edge/{kind}")
def get_graph_by_edge(kind: str) -> JSONResponse:
    graph = _load_graph()
    edges = [e for e in graph["edges"] if e["kind"] == kind]
    if not edges and kind not in {e["kind"] for e in graph["edges"]}:
        raise HTTPException(status_code=404, detail=f"No edges of kind '{kind}'")

    referenced_node_ids = {e["source"] for e in edges} | {e["target"] for e in edges}
    nodes = [n for n in graph["nodes"] if n["id"] in referenced_node_ids]
    return JSONResponse(
        {
            "nodes": nodes,
            "edges": edges,
            "generated_at": graph.get("generated_at"),
            "source": graph.get("source"),
        }
    )


@app.post("/api/lookup")
def post_lookup(req: LookupRequest) -> JSONResponse:
    return JSONResponse(run_lookup(req.situation))


@app.post("/api/briefing")
def post_briefing(req: BriefingRequest) -> JSONResponse:
    return JSONResponse(run_briefing(req.artifact))


# Mount the SPA last so API routes win.
app.mount("/", StaticFiles(directory=str(APP_DIR / "static"), html=True), name="static")
