"""Lookup surface backend.

Given a user's situation in plain text, return a structured response grounded
in the NIL graph: matched concepts, two contrasting takes, the political-
capital tradeoff, and a draft move the user can paste into a doc.

The graph context is built once per process and cached. The Claude system
prompt is also cache-controlled so repeat lookups within an Anthropic
prompt-cache window are cheap.

If ANTHROPIC_API_KEY is not set in the environment, the endpoint falls back
to a deterministic stub so the UI stays testable.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
GRAPH_PATH = APP_DIR / "data" / "graph.json"
PROMPTS_DIR = APP_DIR.parent / "prompts"

_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 1500


class LLMError(Exception):
    """Raised when an LLM call was attempted but failed in a user-visible way.

    Distinct from "stub mode" (no API key, SDK missing) which is silent and
    expected. LLMError surfaces so the frontend can show a real error instead
    of a misleading stub banner.
    """

    def __init__(self, kind: str, detail: str):
        self.kind = kind
        self.detail = detail
        super().__init__(f"{kind}: {detail}")


@lru_cache(maxsize=1)
def _load_graph() -> dict:
    return json.loads(GRAPH_PATH.read_text())


def _system_prompt() -> str:
    # Read on each request so prompt edits land without a server restart.
    return (PROMPTS_DIR / "lookup.txt").read_text()


@lru_cache(maxsize=1)
def graph_context() -> str:
    """Compact JSON projection of the graph for the model.

    For each concept node we attach the artifacts where it appears, with the
    speaker and grounding quote. Trust edges are included as a separate block
    so the model can use them when proposing draft moves that reference how
    one guest cites another.

    Cached, shared across Lookup and Briefing surfaces.
    """

    graph = _load_graph()
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}

    # Map artifact id -> (speaker, title)
    artifact_speakers: dict[str, tuple[str, str]] = {}
    for edge in graph["edges"]:
        if edge["kind"] == "authored_by":
            artifact = nodes_by_id.get(edge["source"])
            person = nodes_by_id.get(edge["target"])
            if artifact and person:
                artifact_speakers[edge["source"]] = (person["label"], artifact["label"])

    # Concept -> [{artifact_id, speaker, quote}]
    concept_appearances: dict[str, list[dict]] = {}
    for edge in graph["edges"]:
        if edge["kind"] != "appears_in":
            continue
        concept_id = edge["source"]
        artifact_id = edge["target"]
        speaker, title = artifact_speakers.get(artifact_id, ("Unknown", artifact_id))
        concept_appearances.setdefault(concept_id, []).append(
            {
                "artifact_id": artifact_id,
                "artifact_title": title,
                "speaker": speaker,
                "quote": (edge.get("meta") or {}).get("quote", ""),
            }
        )

    concepts = []
    for node in graph["nodes"]:
        if node["kind"] != "concept":
            continue
        meta = node.get("meta") or {}
        concepts.append(
            {
                "concept_id": node["id"],
                "canonical_name": node["label"],
                "kind": meta.get("kind", "principle"),
                "one_line": meta.get("one_line", ""),
                "appearances": concept_appearances.get(node["id"], []),
            }
        )

    trust = []
    for edge in graph["edges"]:
        if edge["kind"] != "trust":
            continue
        meta = edge.get("meta") or {}
        source = nodes_by_id.get(edge["source"])
        target = nodes_by_id.get(edge["target"])
        if not source or not target:
            continue
        trust.append(
            {
                "from": source["label"],
                "to": target["label"],
                "artifact_id": meta.get("artifact_id", ""),
                "quote": meta.get("quote", ""),
            }
        )

    return json.dumps({"concepts": concepts, "trust": trust}, indent=2)


def _stub_response(situation: str) -> dict:
    """Deterministic mock used when ANTHROPIC_API_KEY is not set."""

    return {
        "matched_concepts": [
            {
                "concept_id": "concept:vibes-before-evals",
                "why_it_applies": "Stub response. Add ANTHROPIC_API_KEY to Replit secrets to get a real read of your situation.",
            },
        ],
        "contrasting_takes": [
            {
                "speaker": "Howie Liu",
                "artifact_id": "howie-liu",
                "position": "For a novel form factor, start with vibes before formal evals.",
                "quote": "for a completely novel product experience or form factor, you should actually not start with evals and you should start with vibes",
            },
            {
                "speaker": "Hamel Husain & Shreya Shankar",
                "artifact_id": "hamel-husain--shreya-shankar",
                "position": "Vibes are good early but they break down fast at scale.",
                "quote": "vibe checks are good and you should do vibe checks initially, but it can become very unmanageable very fast",
            },
        ],
        "political_capital_tradeoff": (
            "Stub mode is active because ANTHROPIC_API_KEY is not set in Replit secrets. "
            "Add the key and the response will read your actual situation against the live graph."
        ),
        "draft_move": (
            "Add ANTHROPIC_API_KEY in Replit Secrets, restart the workflow, "
            "and re-run this lookup. The same UI will return a grounded read instead of this placeholder."
        ),
        "stub": True,
    }


def _try_real_call(situation: str) -> dict | None:
    """Call Claude. Return None if not configured (stub fallback is correct).

    Raises LLMError if the call was attempted but failed (Anthropic exception,
    non-JSON response). The caller turns LLMError into a structured error
    response so the frontend can distinguish "not configured" from "broken."
    """

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None

    try:
        from anthropic import Anthropic
    except ImportError:
        return None

    client = Anthropic()
    system_prompt = _system_prompt()
    user_content = (
        "<graph>\n"
        f"{graph_context()}\n"
        "</graph>\n\n"
        "<situation>\n"
        f"{situation.strip()}\n"
        "</situation>"
    )

    try:
        response = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=[
                {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}},
            ],
            messages=[{"role": "user", "content": user_content}],
        )
    except Exception as exc:
        raise LLMError("anthropic_error", str(exc)[:300]) from exc

    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError("invalid_json", text[:300]) from exc


def lookup(situation: str) -> dict:
    """Public entry point used by the FastAPI route."""

    situation = (situation or "").strip()
    if not situation:
        return {
            "matched_concepts": [],
            "contrasting_takes": [],
            "political_capital_tradeoff": "Describe the situation you are facing and we will read it against the graph.",
            "draft_move": "",
            "stub": True,
        }

    try:
        real = _try_real_call(situation)
    except LLMError as exc:
        return {
            "matched_concepts": [],
            "contrasting_takes": [],
            "political_capital_tradeoff": (
                f"Lookup failed ({exc.kind}). The graph and prompt loaded but the model "
                "call could not produce a structured result. See error detail below."
            ),
            "draft_move": "",
            "stub": False,
            "error": {"kind": exc.kind, "detail": exc.detail},
        }

    if real is not None:
        real.setdefault("stub", False)
        return real

    return _stub_response(situation)
