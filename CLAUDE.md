# CLAUDE.md

Notes for the next Claude session in this repo.

## What this is

Ian's entry for the Lenny's Newsletter x Replit Buildathon. A Network Intelligence Layer (NIL) graph extracted offline from Lenny Rachitsky's open podcast and newsletter archive, plus three runtime surfaces that read external inputs against the graph.

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

Replit workflow: `Start application` (port 5000, webview).

To rebuild the graph from source:

```bash
python -m extraction.run --starter-pack data/starter-pack --out app/data/graph.json
```

## Surfaces

Three tabs in `app/static/index.html`. All three share the graph context.

- **Atlas** (`graph.js`) — vis-network force-directed graph of the NIL. Pure client-side render of `app/data/graph.json`. No LLM at runtime.
- **Lookup** (`lookup.js` ↔ `app/lookup.py` ↔ `prompts/lookup.txt`) — user pastes a situation, model returns a structured read with two contrasting takes plus a draft move. LLM at runtime.
- **Briefing** (`briefing.js` ↔ `app/briefing.py` ↔ `prompts/briefing.txt`) — user pastes an external artifact (CPO talk, JD, board doc, post), model returns summary + priorities (with corpus agree/pushback) + questions. LLM at runtime.

Lookup and Briefing share `graph_context()` from `app/lookup.py` so the Anthropic prompt cache hits across both surfaces within a 5-minute window.

## Where things live

- `app/main.py` — FastAPI; routes `/api/graph`, `/api/graph/by-edge/{kind}`, `/api/lookup`, `/api/briefing`. Mounts `app/static/` last.
- `app/lookup.py`, `app/briefing.py` — runtime LLM callers. Stub fallback when `ANTHROPIC_API_KEY` is unset.
- `app/static/` — `index.html`, `style.css`, `vis-network.min.js`, plus one JS file per surface.
- `app/data/graph.json` — pre-built NIL graph. Committed.
- `prompts/*.txt` — system prompts. `briefing.txt` and `lookup.txt` are runtime; `shared_language.txt` and `trust_signals.txt` are used by the offline extraction pipeline.
- `extraction/` — offline pipeline that builds `graph.json` from `data/starter-pack/`.
- `data/starter-pack/{posts,transcripts}/` — markdown sources.
- `data/extracted/` — gitignored intermediate JSONL.
- `eval/` — eval harness and audit notes for the runtime surfaces.

## Architecture decisions

- **Graph is offline.** `extraction.run` writes `app/data/graph.json`; the Atlas tab never calls an LLM. The graph file IS committed.
- **vis-network is local**, not CDN. Hosted preview iframes break with CDN scripts. If upgrading, replace `app/static/vis-network.min.js` directly.
- **Runtime prompts are NOT cached in-process.** `_system_prompt()` in `app/briefing.py` and `app/lookup.py` reads the file on every call. Edits to `prompts/*.txt` land without a server restart. (See git history: removing `lru_cache` was the fix.) The graph IS still cached because it only changes via the offline rebuild.
- **Anthropic prompt-cache**: `system` is sent with `cache_control: {"type": "ephemeral"}` so the system prompt + (per-surface) graph context hits the 5-minute cache. Prompt edits bust the cache; that's expected during iteration.
- **Stub mode** kicks in when `ANTHROPIC_API_KEY` is missing, the SDK fails to import, the call throws, or the response is non-JSON. All four collapse into the same stub response — see `eval/briefing_surface_audit.md` for why that's a UX bug.
- **vis-network gotcha**: `#graph` has `min-height: 500px` in addition to `calc(100vh - 120px)` because `100vh` resolves to ~0 inside preview iframes. Also `network.destroy()` before each `renderGraph()` and `network.fit()` immediately after construction.

## Prompt iteration loop

The Briefing prompt is the active iteration target. Workflow:

1. Edit `prompts/briefing.txt`. No server restart needed.
2. Re-run an artifact through the Briefing tab in the browser, OR
3. Run the eval harness for mechanical checks:

   ```bash
   python -m eval.check_briefing eval/fixtures/hibob_pm_payroll.txt
   # or check a saved JSON brief without making a model call:
   python -m eval.check_briefing eval/fixtures/hibob_pm_payroll.txt --brief eval/fixtures/hibob_brief_iter2.json
   ```

The harness checks: evidence_quote ≤15 words, verbatim from artifact, not duplicated as a bullet, agree/pushback quotes verbatim from graph, frame-word imports (AI/platform/ecosystem/moat) only if present in artifact, 4-priority cap, 0-2 entries per agree/pushback, 3-5 questions, no em dashes, no banned phrases.

The harness does NOT check the semantic rules: whole-document hedging, signal-rich phrasing preference, broadening test for pushback "why" sentences. Those still need eyeballing.

## Gotchas

- Always re-run `python -m extraction.run` after touching `data/starter-pack/` to regenerate `app/data/graph.json`.
- The Anthropic model is hardcoded as `claude-sonnet-4-6` in both `app/briefing.py:23` and `app/lookup.py:26`. If migrating models, update both.
- `app/briefing.py` imports `graph_context` from `app/lookup.py`. The graph projection lives in lookup.py for historical reasons; if refactoring, both surfaces depend on the same shape.
- The frontend `nodeLabel()` in `briefing.js` and `lookup.js` reads `window.fullGraph`, populated by `graph.js` on mount. If a user submits before Atlas finishes loading, evidence cards lose the artifact title and fall back to the id. See `eval/briefing_surface_audit.md` item 4.

## Development branch

Active branch for ongoing work: `claude/newsletter-contest-project-CxDag`. Push there.
