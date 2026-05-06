"""Thin Anthropic wrapper used by the extractors.

Reads ANTHROPIC_API_KEY from the environment. Uses prompt caching on the
system prompt so re-running extraction across many artifacts stays cheap.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from anthropic import Anthropic

_DEFAULT_MODEL = "claude-sonnet-4-6"
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / f"{name}.txt").read_text()


def extract_json(
    *,
    prompt_name: str,
    artifact_text: str,
    artifact_meta: dict,
    model: str = _DEFAULT_MODEL,
    max_tokens: int = 2048,
) -> dict:
    """Run an extraction prompt against one artifact and return parsed JSON.

    The system prompt is cached so subsequent calls within the run are cheap.
    The artifact body is sent in the user turn so it stays out of the cache.
    """

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    system_prompt = _load_prompt(prompt_name)

    meta_block = json.dumps(artifact_meta, indent=2)
    user_content = (
        "<artifact_meta>\n"
        f"{meta_block}\n"
        "</artifact_meta>\n\n"
        "<artifact_text>\n"
        f"{artifact_text}\n"
        "</artifact_text>"
    )

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_content}],
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    return _parse_json(text)


def _parse_json(text: str) -> dict:
    """Be forgiving about model output that wraps JSON in code fences."""

    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.strip()
    return json.loads(stripped)
