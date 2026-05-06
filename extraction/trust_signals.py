"""Extract trust edges between named people from one artifact."""

from __future__ import annotations

from .llm import extract_json
from .types import Artifact, TrustEdge


def extract_trust_edges(artifact: Artifact, body: str) -> list[TrustEdge]:
    speaker = artifact.guest or "Lenny Rachitsky"

    payload = extract_json(
        prompt_name="trust_signals",
        artifact_text=body,
        artifact_meta={
            "title": artifact.title,
            "type": artifact.type.value,
            "speaker_name": speaker,
            "date": artifact.date,
        },
    )

    edges: list[TrustEdge] = []
    for raw in payload.get("trust_edges", []):
        source = (raw.get("source_person") or speaker).strip()
        target = (raw.get("target_person") or "").strip()
        if not target or source.lower() == target.lower():
            continue
        edges.append(
            TrustEdge(
                source_person=source,
                target_person=target,
                artifact_id=artifact.id,
                quote=raw.get("quote", ""),
            )
        )
    return edges
