"""Briefing surface backend.

Given an external artifact pasted by the user (CPO talk, JD, board doc), read
it against the NIL graph and return a structured briefing: summary, priorities
with corpus agreement and pushback, and questions to ask.

Mirrors the shape of app.lookup. Shares the cached graph_context() so the
prompt-cache hit on the system prompt and graph context carries across both
surfaces within an Anthropic prompt-cache window.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .lookup import LLMError, extract_json_object, graph_context

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 2500


def _system_prompt() -> str:
    # Read on each request so prompt edits land without a server restart.
    return (PROMPTS_DIR / "briefing.txt").read_text()


def _stub_response(artifact: str) -> dict:
    return {
        "summary": (
            "Stub mode is active because ANTHROPIC_API_KEY is not set in Replit secrets. "
            "Add the key and the briefing will read your pasted artifact against the live graph."
        ),
        "priorities": [
            {
                "priority": "Ship under research-preview labels to learn from real usage.",
                "evidence_quote": "(stub) replace with verbatim text from the artifact.",
                "agrees": [
                    {
                        "speaker": "Cat Wu",
                        "artifact_id": "cat-wu",
                        "quote": "we ship almost all of our features in research preview",
                        "why": "Stub. The corpus has direct support for staged exposure under a research-preview label.",
                    }
                ],
                "pushes_back": [
                    {
                        "speaker": "Hamel Husain & Shreya Shankar",
                        "artifact_id": "hamel-husain--shreya-shankar",
                        "quote": "vibe checks are good and you should do vibe checks initially, but it can become very unmanageable very fast",
                        "why": "Stub. The corpus warns that early-stage shipping rituals do not scale without eval discipline.",
                    }
                ],
            }
        ],
        "questions_to_ask": [
            "Stub. Add ANTHROPIC_API_KEY in Replit Secrets and restart the workflow for a real briefing.",
        ],
        "stub": True,
    }


def _try_real_call(artifact: str) -> dict | None:
    """Returns the parsed brief on success, None when stub fallback is appropriate.

    Raises LLMError when the call was attempted but failed (Anthropic exception
    or non-JSON response) so the caller can return a distinct error response
    instead of silently masquerading as stub mode.
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
        "<artifact>\n"
        f"{artifact.strip()}\n"
        "</artifact>"
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

    text = "".join(block.text for block in response.content if block.type == "text")
    text = extract_json_object(text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError("invalid_json", text[:300]) from exc


def briefing(artifact: str) -> dict:
    """Public entry point used by the FastAPI route."""

    artifact = (artifact or "").strip()
    if not artifact:
        return {
            "summary": "Paste an external artifact (a CPO talk, JD, board doc, or post) and we will read it against the graph.",
            "priorities": [],
            "questions_to_ask": [],
            "stub": True,
        }

    try:
        real = _try_real_call(artifact)
    except LLMError as exc:
        return {
            "summary": (
                f"Briefing failed ({exc.kind}). The graph and prompt loaded, but the model "
                "call could not produce a structured result."
            ),
            "priorities": [],
            "questions_to_ask": [],
            "stub": False,
            "error": {"kind": exc.kind, "detail": exc.detail},
        }

    if real is not None:
        real.setdefault("stub", False)
        return real

    return _stub_response(artifact)
