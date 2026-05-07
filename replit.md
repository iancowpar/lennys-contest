# Beneath the Org Chart

A single-page app built on a Network Intelligence Layer (NIL) graph extracted from Lenny Rachitsky's open podcast and newsletter archive. Three surfaces:

- **Atlas** — force-directed graph view of the NIL.
- **Lookup** — paste a situation, get a structured read with two contrasting takes and a draft move.
- **Briefing** — paste an external artifact (CPO talk, JD, board doc, post), get a summary, priorities with corpus agree/pushback, and questions to ask.

## Run & Operate

```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

Workflow: `Start application` (port 5000, webview).

Set `ANTHROPIC_API_KEY` in Replit secrets to enable Lookup and Briefing. Without it, both surfaces return a stub response.

To rebuild the graph from source: `python -m extraction.run`

## Stack

- Python 3.11, FastAPI, Uvicorn, Anthropic SDK
- vis-network 9.1.9 (bundled locally at `app/static/vis-network.min.js`)
- Vanilla JS / CSS frontend (no build step)

## Where things live

- `app/main.py` — FastAPI server; routes `/api/graph`, `/api/graph/by-edge/{kind}`, `/api/lookup`, `/api/briefing`. Mounts the static SPA.
- `app/lookup.py`, `app/briefing.py` — runtime LLM callers, sharing `graph_context()`.
- `app/static/` — `index.html`, `style.css`, `vis-network.min.js`, plus `graph.js` / `lookup.js` / `briefing.js` / `main.js`.
- `app/data/graph.json` — pre-built NIL graph (nodes + edges).
- `prompts/` — `briefing.txt` and `lookup.txt` are runtime system prompts; `shared_language.txt` and `trust_signals.txt` are used by the offline extraction pipeline.
- `extraction/` — offline pipeline that builds `graph.json` from `data/starter-pack/`.
- `eval/` — eval harness (`check_briefing.py`) and audit notes for the runtime surfaces.

## Architecture decisions

- Graph is generated **offline** (`extraction.run`) and shipped as static JSON; the Atlas surface never calls an LLM.
- The runtime surfaces (Lookup, Briefing) call Anthropic with the system prompt cached via `cache_control: ephemeral` so the prompt + graph context hits the 5-minute prompt cache across both surfaces.
- Runtime prompts are **read on every request** (no in-process cache). Edits to `prompts/*.txt` land without a server restart.
- vis-network is served **locally** (not from a CDN) to avoid availability/network issues in hosted environments.
- `#graph` container uses `min-height: 500px` in addition to `calc(100vh - 120px)` because `100vh` can resolve to ~0 inside a preview iframe, causing vis-network to create a zero-size canvas and render nothing.
- `network.destroy()` is called before each `renderGraph` to avoid multiple Network instances on the same DOM node.
- `network.fit()` is called immediately after construction so nodes are visible before physics settles.

## Product

- Atlas: force-directed network graph of concepts, people, and artifacts. Filter buttons: **Shared language**, **Trust**, **All**. Click any node or edge to see detail in the side panel.
- Lookup: situation in, structured read out (two contrasting takes + political-capital tradeoff + draft move).
- Briefing: artifact in, structured briefing out (summary + priorities with corpus agree/pushback + questions to ask).

## Gotchas

- Always re-run `python -m extraction.run` after updating `data/starter-pack/` to regenerate `app/data/graph.json`.
- vis-network CDN was replaced with a local copy; if upgrading the library, re-download and replace `app/static/vis-network.min.js`.
- Stub mode swallows several distinct failure modes (missing API key, SDK import error, Anthropic exception, malformed JSON). See `eval/briefing_surface_audit.md` for the punch list.
