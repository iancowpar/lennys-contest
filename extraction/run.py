"""End-to-end build entry point.

Usage:
  python -m extraction.run --starter-pack data/starter-pack --out app/data/graph.json

Reads markdown from --starter-pack, runs shared-language and trust-signal
extraction against each artifact, and writes the combined graph JSON.

Supports incremental/checkpoint mode: after each artifact a checkpoint file
is written so the run can be resumed if interrupted.  Pass --checkpoint
(default: .extraction_checkpoint.json) to control the path; pass --fresh
to ignore any existing checkpoint and start over.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .build_graph import build_graph, write_graph
from .ingest import load_artifacts
from .shared_language import extract_concepts
from .trust_signals import extract_trust_edges
from .types import Concept, ConceptMention, TrustEdge

log = logging.getLogger("extract")

_CHECKPOINT_VERSION = 1


def _load_checkpoint(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        if data.get("version") != _CHECKPOINT_VERSION:
            log.warning("Checkpoint version mismatch — ignoring")
            return None
        return data
    except Exception as e:
        log.warning("Could not read checkpoint %s: %s", path, e)
        return None


def _save_checkpoint(
    path: Path,
    done_ids: set[str],
    concepts_by_artifact: dict,
    all_mentions: list,
    all_trust: list,
) -> None:
    data = {
        "version": _CHECKPOINT_VERSION,
        "done_ids": list(done_ids),
        "concepts_by_artifact": {
            k: [c.model_dump() for c in v]
            for k, v in concepts_by_artifact.items()
        },
        "all_mentions": [m.model_dump() for m in all_mentions],
        "all_trust": [t.model_dump() for t in all_trust],
    }
    path.write_text(json.dumps(data))


def _restore_checkpoint(data: dict) -> tuple[set[str], dict, list, list]:
    done_ids = set(data["done_ids"])
    concepts_by_artifact = {
        k: [Concept(**c) for c in v]
        for k, v in data["concepts_by_artifact"].items()
    }
    all_mentions = [ConceptMention(**m) for m in data["all_mentions"]]
    all_trust = [TrustEdge(**t) for t in data["all_trust"]]
    return done_ids, concepts_by_artifact, all_mentions, all_trust


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
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path(".extraction_checkpoint.json"),
        help="Path to the incremental checkpoint file.",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore any existing checkpoint and start from scratch.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    artifacts, bodies = load_artifacts(args.starter_pack)
    if args.limit:
        artifacts = artifacts[: args.limit]
    log.info("Loaded %d artifacts", len(artifacts))

    concepts_by_artifact: dict[str, list[Concept]] = {}
    all_mentions: list[ConceptMention] = []
    all_trust: list[TrustEdge] = []
    done_ids: set[str] = set()

    # Restore checkpoint if available
    if not args.fresh:
        ckpt = _load_checkpoint(args.checkpoint)
        if ckpt:
            done_ids, concepts_by_artifact, all_mentions, all_trust = _restore_checkpoint(ckpt)
            log.info("Resumed from checkpoint: %d/%d artifacts already done", len(done_ids), len(artifacts))

    total = len(artifacts)
    for i, artifact in enumerate(artifacts, start=1):
        if artifact.id in done_ids:
            log.info("[%d/%d] SKIP (cached) %s", i, total, artifact.title)
            continue

        body = bodies[artifact.id]
        log.info("[%d/%d] %s", i, total, artifact.title)

        concepts, mentions = extract_concepts(artifact, body)
        concepts_by_artifact[artifact.id] = concepts
        all_mentions.extend(mentions)

        trust_edges = extract_trust_edges(artifact, body)
        all_trust.extend(trust_edges)

        done_ids.add(artifact.id)
        _save_checkpoint(args.checkpoint, done_ids, concepts_by_artifact, all_mentions, all_trust)

        # Write partial graph so the app stays live as processing continues
        done_artifacts = [a for a in artifacts if a.id in done_ids]
        partial = build_graph(
            artifacts=done_artifacts,
            concepts_by_artifact=concepts_by_artifact,
            mentions=all_mentions,
            trust_edges=all_trust,
            source=args.source,
        )
        write_graph(partial, args.out)
        log.info("  → partial graph: %d nodes, %d edges", len(partial.nodes), len(partial.edges))

    graph = build_graph(
        artifacts=artifacts,
        concepts_by_artifact=concepts_by_artifact,
        mentions=all_mentions,
        trust_edges=all_trust,
        source=args.source,
    )
    write_graph(graph, args.out)
    log.info("Wrote %s with %d nodes and %d edges", args.out, len(graph.nodes), len(graph.edges))

    # Clean up checkpoint on successful completion
    if args.checkpoint.exists():
        args.checkpoint.unlink()
        log.info("Checkpoint cleared")


if __name__ == "__main__":
    main()
