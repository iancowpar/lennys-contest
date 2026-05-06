"""Extract named frameworks, principles, metrics, and metaphors from one artifact."""

from __future__ import annotations

import re

from .llm import extract_json
from .types import Artifact, Concept, ConceptMention


def _concept_id(canonical_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", canonical_name.lower()).strip("-")
    return f"concept:{slug}"


def extract_concepts(
    artifact: Artifact, body: str
) -> tuple[list[Concept], list[ConceptMention]]:
    """Run the shared-language prompt and return (concepts, mentions)."""

    payload = extract_json(
        prompt_name="shared_language",
        artifact_text=body,
        artifact_meta={
            "title": artifact.title,
            "type": artifact.type.value,
            "guest": artifact.guest,
            "date": artifact.date,
        },
    )

    concepts: list[Concept] = []
    mentions: list[ConceptMention] = []

    for raw in payload.get("concepts", []):
        name = (raw.get("canonical_name") or "").strip()
        if not name:
            continue

        cid = _concept_id(name)
        concepts.append(
            Concept(
                id=cid,
                canonical_name=name,
                aliases=[a.strip() for a in raw.get("aliases", []) if a.strip()],
                kind=raw.get("kind", "principle"),
                one_line=raw.get("one_line", ""),
            )
        )
        mentions.append(
            ConceptMention(
                concept_id=cid,
                artifact_id=artifact.id,
                quote=raw.get("quote", ""),
            )
        )

    return concepts, mentions
