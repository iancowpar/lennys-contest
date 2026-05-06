# Beneath the Org Chart

A single-page app that visualises a Network Intelligence Layer (NIL) graph built from Lenny Rachitsky's open podcast archive.

## Run & Operate

```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

Workflow: `Start application` (port 5000, webview).

To rebuild the graph from source: `python -m extraction.run`

## Stack

- Python 3.11, FastAPI, Uvicorn
- vis-network 9.1.9 (bundled locally at `app/static/vis-network.min.js`)
- Vanilla JS / CSS frontend (no build step)

## Where things live

- `app/main.py` — FastAPI server; serves `/api/graph` and mounts static SPA
- `app/static/` — `index.html`, `graph.js`, `style.css`, `vis-network.min.js`
- `app/data/graph.json` — pre-built NIL graph (nodes + edges)
- `extraction/` — offline pipeline that builds `graph.json` from RSS + LLM

## Architecture decisions

- Graph is generated **offline** (`extraction.run`) and shipped as static JSON; the runtime never calls an LLM.
- vis-network is served **locally** (not from a CDN) to avoid availability/network issues in hosted environments.
- `#graph` container uses `min-height: 500px` in addition to `calc(100vh - 120px)` because `100vh` can resolve to ~0 inside a preview iframe, causing vis-network to create a zero-size canvas and render nothing.
- `network.destroy()` is called before each `renderGraph` to avoid multiple Network instances on the same DOM node.
- `network.fit()` is called immediately after construction so nodes are visible before physics settles.

## Product

- Force-directed network graph of concepts, people, and artifacts extracted from podcast episodes
- Filter buttons: **Shared language**, **Trust**, **All**
- Click any node or edge to see detail in the side panel

## Gotchas

- Always re-run `python -m extraction.run` after updating `research/` content to regenerate `app/data/graph.json`.
- vis-network CDN was replaced with a local copy; if upgrading the library, re-download and replace `app/static/vis-network.min.js`.
