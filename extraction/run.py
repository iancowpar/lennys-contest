"""End-to-end build entry point.

Usage:
  python -m extraction.run --starter-pack data/starter-pack --out app/data/graph.json

Reads markdown from --starter-pack, runs shared-language and trust-signal
extraction against each artifact, and writes the combined graph JSON.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .build_graph import build_graph, write_graph
from .ingest import load_artifacts
from .shared_language import extract_concepts
from .trust_signals import extract_trust_edges
from .types import Concept, ConceptMention, TrustEdge

log = logging.getLogger("extract")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starter-pack", type=Path, default=Path("data/starter-pack"))
    parser.add_argument("--out", type=Path, default=Path("app/data/graph.json"))
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="If > 0, only process the first N artifacts (for fast iteration).",
    )
    parser.add_argument("--source", default="starter-pack")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    artifacts, bodies = load_artifacts(args.starter_pack)
    if args.limit:
        artifacts = artifacts[: args.limit]
    log.info("Loaded %d artifacts", len(artifacts))

    concepts_by_artifact: dict[str, list[Concept]] = {}
    all_mentions: list[ConceptMention] = []
    all_trust: list[TrustEdge] = []

    for i, artifact in enumerate(artifacts, start=1):
        body = bodies[artifact.id]
        log.info("[%d/%d] %s", i, len(artifacts), artifact.title)

        concepts, mentions = extract_concepts(artifact, body)
        concepts_by_artifact[artifact.id] = concepts
        all_mentions.extend(mentions)

        trust_edges = extract_trust_edges(artifact, body)
        all_trust.extend(trust_edges)

    graph = build_graph(
        artifacts=artifacts,
        concepts_by_artifact=concepts_by_artifact,
        mentions=all_mentions,
        trust_edges=all_trust,
        source=args.source,
    )
    write_graph(graph, args.out)
    log.info("Wrote %s with %d nodes and %d edges", args.out, len(graph.nodes), len(graph.edges))


if __name__ == "__main__":
    main()
