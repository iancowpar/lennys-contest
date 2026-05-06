"""Seed graph generator.

Builds app/data/graph.json from a small set of hand-curated extractions taken
verbatim from four starter-pack podcasts. We use this so the demo renders a
real, grounded graph before the LLM extraction has been wired up against an
actual ANTHROPIC_API_KEY.

Once `python -m extraction.run` runs against the full starter pack, this seed
output is replaced. Until then, this gives us a deployable artifact end-to-end.
"""

from __future__ import annotations

from pathlib import Path

from .build_graph import build_graph, write_graph
from .types import (
    Artifact,
    ArtifactType,
    Concept,
    ConceptMention,
    TrustEdge,
)

ARTIFACTS = [
    Artifact(
        id="cat-wu",
        title="How Anthropic's product team moves faster than anyone else",
        filename="podcasts/cat-wu.md",
        type=ArtifactType.PODCAST,
        date="2026-04-23",
        word_count=16271,
        guest="Cat Wu",
        tags=["leadership", "ai", "product-management"],
    ),
    Artifact(
        id="nikhyl-singhal-2",
        title="Why half of product managers are in trouble",
        filename="podcasts/nikhyl-singhal-2.md",
        type=ArtifactType.PODCAST,
        date="2026-04-19",
        word_count=17206,
        guest="Nikhyl Singhal",
        tags=["product-management", "career", "ai"],
    ),
    Artifact(
        id="amol-avasare",
        title="How Claude became the fastest-growing AI product in history",
        filename="podcasts/amol-avasare.md",
        type=ArtifactType.PODCAST,
        date="2026-04-05",
        word_count=22125,
        guest="Amol Avasare",
        tags=["growth", "ai", "pricing"],
    ),
    Artifact(
        id="evan-spiegel",
        title="Why distribution has become the most important moat",
        filename="podcasts/evan-spiegel.md",
        type=ArtifactType.PODCAST,
        date="2026-04-26",
        word_count=14177,
        guest="Evan Spiegel",
        tags=["b2c", "strategy", "go-to-market"],
    ),
]


def _concept(id_suffix: str, name: str, kind: str, one_line: str) -> Concept:
    return Concept(
        id=f"concept:{id_suffix}",
        canonical_name=name,
        kind=kind,
        one_line=one_line,
    )


# Concepts grounded in observed transcript text. Quotes are short paraphrases
# of what the speaker actually said, suitable as hover content.
RESEARCH_PREVIEW = _concept(
    "research-preview",
    "Research preview",
    "principle",
    "Ship features under a research-preview label so the team can move fast without committing to long-term support.",
)

EVERGREEN_LAUNCH_ROOM = _concept(
    "evergreen-launch-room",
    "Evergreen launch room",
    "framework",
    "A standing channel where engineering, docs, marketing, and DevRel coordinate launches in a day instead of a week.",
)

TEAM_PRINCIPLES = _concept(
    "team-principles",
    "Team principles",
    "framework",
    "A written list of who the team's users are and what tradeoffs the team will make, so people can decide without escalation.",
)

AI_FIRST = _concept(
    "ai-first",
    "AI-first",
    "principle",
    "Hire and operate as if AI is the default tool, not the optional one. Companies will shed staff and rehire AI-first.",
)

BUILDERS = _concept(
    "the-builders",
    "The builders",
    "principle",
    "PMs whose value is making things, not just shaping things. The next two years reward builders and punish the rest.",
)

PM_SLOP_CANNON = _concept(
    "pm-slop-cannon",
    "PM slop-cannon",
    "metaphor",
    "A vivid label for the PM whose only output is volume of low-signal artifacts. Used as a warning, not a compliment.",
)

DISTRIBUTION_AS_MOAT = _concept(
    "distribution-as-moat",
    "Distribution as moat",
    "principle",
    "In a world where capability gets commoditized, the durable advantage is whether you can reach people at all.",
)

THROW_IT_OUT = _concept(
    "throw-it-out",
    "Throw it out the door",
    "principle",
    "Operating inside an AI company means 50-70% of how you operated before is no longer load-bearing. Discard it.",
)


CONCEPTS_BY_ARTIFACT: dict[str, list[Concept]] = {
    "cat-wu": [RESEARCH_PREVIEW, EVERGREEN_LAUNCH_ROOM, TEAM_PRINCIPLES, AI_FIRST],
    "nikhyl-singhal-2": [AI_FIRST, BUILDERS, PM_SLOP_CANNON],
    "amol-avasare": [AI_FIRST, DISTRIBUTION_AS_MOAT, THROW_IT_OUT],
    "evan-spiegel": [DISTRIBUTION_AS_MOAT],
}


MENTIONS = [
    ConceptMention(
        concept_id=RESEARCH_PREVIEW.id,
        artifact_id="cat-wu",
        quote="we ship almost all of our features in research preview",
    ),
    ConceptMention(
        concept_id=EVERGREEN_LAUNCH_ROOM.id,
        artifact_id="cat-wu",
        quote="they post it in our evergreen launch room",
    ),
    ConceptMention(
        concept_id=TEAM_PRINCIPLES.id,
        artifact_id="cat-wu",
        quote="we have this list of team principles",
    ),
    ConceptMention(
        concept_id=AI_FIRST.id,
        artifact_id="cat-wu",
        quote="ship something almost all in research preview",
    ),
    ConceptMention(
        concept_id=AI_FIRST.id,
        artifact_id="nikhyl-singhal-2",
        quote="the 8,000 people are going to all be AI first",
    ),
    ConceptMention(
        concept_id=BUILDERS.id,
        artifact_id="nikhyl-singhal-2",
        quote="the builders are going to have the time of their lives",
    ),
    ConceptMention(
        concept_id=PM_SLOP_CANNON.id,
        artifact_id="nikhyl-singhal-2",
        quote="PM slop-cannon",
    ),
    ConceptMention(
        concept_id=AI_FIRST.id,
        artifact_id="amol-avasare",
        quote="50%, 60%, 70% of how you operate in the past, just throw it out",
    ),
    ConceptMention(
        concept_id=DISTRIBUTION_AS_MOAT.id,
        artifact_id="amol-avasare",
        quote="we didn't have the free cash flow or the distribution of a Meta or Google",
    ),
    ConceptMention(
        concept_id=THROW_IT_OUT.id,
        artifact_id="amol-avasare",
        quote="50%, 60%, 70% of how you operate in the past, just throw it out the door",
    ),
    ConceptMention(
        concept_id=DISTRIBUTION_AS_MOAT.id,
        artifact_id="evan-spiegel",
        quote="why distribution has become the most important moat",
    ),
]


TRUST_EDGES = [
    TrustEdge(
        source_person="Lenny Rachitsky",
        target_person="Nikhyl Singhal",
        artifact_id="nikhyl-singhal-2",
        quote="Nikhyl is, in my opinion, right now, the number one person to learn from on PM craft.",
    ),
    TrustEdge(
        source_person="Lenny Rachitsky",
        target_person="Amol Avasare",
        artifact_id="amol-avasare",
        quote="Amol leads growth at Anthropic during the fastest run in software history.",
    ),
]


def main() -> None:
    out_path = Path(__file__).resolve().parent.parent / "app" / "data" / "graph.json"
    graph = build_graph(
        artifacts=ARTIFACTS,
        concepts_by_artifact=CONCEPTS_BY_ARTIFACT,
        mentions=MENTIONS,
        trust_edges=TRUST_EDGES,
        source="seed:starter-pack-sample",
    )
    write_graph(graph, out_path)
    print(f"Wrote seed graph to {out_path}")
    print(f"  Nodes: {len(graph.nodes)}")
    print(f"  Edges: {len(graph.edges)}")


if __name__ == "__main__":
    main()
