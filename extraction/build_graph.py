"""Combine ingest output and per-artifact extractions into a single graph JSON.

Run order:
  1. ingest.load_artifacts -> Artifact records and bodies
  2. shared_language.extract_concepts -> Concepts and ConceptMentions per artifact
  3. trust_signals.extract_trust_edges -> TrustEdges per artifact
  4. build_graph.build_graph -> Graph (nodes + edges)
  5. write graph.json into app/data/

The build is deterministic given the same inputs. Concept dedupe is by id
(slug of canonical_name); we collapse aliases observed across artifacts onto
the first record we saw.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from collections import defaultdict
from pathlib import Path

from .types import (
    Artifact,
    Concept,
    ConceptMention,
    EdgeKind,
    Graph,
    GraphEdge,
    GraphNode,
    NodeKind,
    TrustEdge,
)


def _person_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"person:{slug}"


def build_graph(
    *,
    artifacts: list[Artifact],
    concepts_by_artifact: dict[str, list[Concept]],
    mentions: list[ConceptMention],
    trust_edges: list[TrustEdge],
    source: str,
) -> Graph:
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []

    # 1. Artifact and Person nodes, plus AUTHORED_BY edges.
    for artifact in artifacts:
        nodes[artifact.id] = GraphNode(
            id=artifact.id,
            label=artifact.title,
            kind=NodeKind.ARTIFACT,
            meta={
                "type": artifact.type.value,
                "date": artifact.date,
                "tags": artifact.tags,
                "source_url": artifact.source_url,
            },
        )

        speaker = artifact.guest or "Lenny Rachitsky"
        pid = _person_id(speaker)
        if pid not in nodes:
            nodes[pid] = GraphNode(id=pid, label=speaker, kind=NodeKind.PERSON, meta={})

        edges.append(
            GraphEdge(
                source=artifact.id,
                target=pid,
                kind=EdgeKind.AUTHORED_BY,
            )
        )

    # 2. Concept nodes, deduped by id. Collapse aliases observed across runs.
    canonical: dict[str, Concept] = {}
    for concept_list in concepts_by_artifact.values():
        for concept in concept_list:
            existing = canonical.get(concept.id)
            if existing is None:
                canonical[concept.id] = concept
                continue
            merged_aliases = sorted(set(existing.aliases) | set(concept.aliases))
            canonical[concept.id] = existing.model_copy(update={"aliases": merged_aliases})

    for concept in canonical.values():
        nodes[concept.id] = GraphNode(
            id=concept.id,
            label=concept.canonical_name,
            kind=NodeKind.CONCEPT,
            meta={
                "kind": concept.kind,
                "one_line": concept.one_line,
                "aliases": concept.aliases,
            },
        )

    # 3. APPEARS_IN edges (Concept -> Artifact) carry the grounding quote.
    artifact_concepts: dict[str, set[str]] = defaultdict(set)
    for mention in mentions:
        if mention.concept_id not in canonical:
            continue
        edges.append(
            GraphEdge(
                source=mention.concept_id,
                target=mention.artifact_id,
                kind=EdgeKind.APPEARS_IN,
                meta={"quote": mention.quote},
            )
        )
        artifact_concepts[mention.artifact_id].add(mention.concept_id)

    # 4. SHARED_LANGUAGE edges: Concept <-> Concept co-occurrence within artifact.
    pair_weights: dict[tuple[str, str], float] = defaultdict(float)
    for concept_ids in artifact_concepts.values():
        ids = sorted(concept_ids)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pair_weights[(ids[i], ids[j])] += 1.0
    for (a, b), weight in pair_weights.items():
        edges.append(
            GraphEdge(source=a, target=b, kind=EdgeKind.SHARED_LANGUAGE, weight=weight)
        )

    # 5. TRUST edges: Person -> Person, with the artifact and quote attached.
    for trust in trust_edges:
        src = _person_id(trust.source_person)
        tgt = _person_id(trust.target_person)
        for pid, pname in ((src, trust.source_person), (tgt, trust.target_person)):
            if pid not in nodes:
                nodes[pid] = GraphNode(id=pid, label=pname, kind=NodeKind.PERSON, meta={})
        edges.append(
            GraphEdge(
                source=src,
                target=tgt,
                kind=EdgeKind.TRUST,
                meta={"artifact_id": trust.artifact_id, "quote": trust.quote},
            )
        )

    return Graph(
        nodes=list(nodes.values()),
        edges=edges,
        generated_at=dt.datetime.now(dt.UTC).isoformat(),
        source=source,
    )


def write_graph(graph: Graph, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(graph.model_dump(), indent=2))
