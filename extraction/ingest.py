"""Read raw markdown files from data/starter-pack and normalize them into Artifacts.

The starter pack ships markdown with YAML frontmatter (title, date, tags, guest,
subtitle, source_url, etc). We hand back a list of Artifact records plus the
markdown body keyed by artifact id, so downstream extractors can run prompts
against the body without re-parsing.
"""

from __future__ import annotations

import re
from pathlib import Path

import frontmatter

from .types import Artifact, ArtifactType


def _slug_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    return re.sub(r"[^a-z0-9-]", "-", stem.lower()).strip("-")


def load_artifacts(starter_pack_dir: Path) -> tuple[list[Artifact], dict[str, str]]:
    """Read all markdown under starter_pack_dir and return (artifacts, body_by_id)."""

    artifacts: list[Artifact] = []
    bodies: dict[str, str] = {}

    for md_path in sorted(starter_pack_dir.rglob("*.md")):
        post = frontmatter.load(md_path)
        meta = post.metadata
        body = post.content

        rel_filename = str(md_path.relative_to(starter_pack_dir))
        artifact_type = (
            ArtifactType.PODCAST
            if "podcasts" in rel_filename
            else ArtifactType.NEWSLETTER
        )

        artifact_id = _slug_from_filename(rel_filename)

        artifact = Artifact(
            id=artifact_id,
            title=meta.get("title") or md_path.stem,
            filename=rel_filename,
            type=artifact_type,
            date=meta.get("date"),
            word_count=meta.get("word_count"),
            tags=list(meta.get("tags") or []),
            guest=meta.get("guest"),
            subtitle=meta.get("subtitle"),
            source_url=meta.get("source_url") or meta.get("post_url"),
        )

        artifacts.append(artifact)
        bodies[artifact.id] = body

    return artifacts, bodies
