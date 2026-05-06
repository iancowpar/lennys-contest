"""Core data types shared across the extraction pipeline.

The graph has three node kinds:
- Artifact: one newsletter post or podcast transcript.
- Person: a podcast guest or newsletter author.
- Concept: a named framework, principle, or recurring pattern extracted from an artifact.

Edges carry a NIL dimension so the frontend can filter by edge type.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    NEWSLETTER = "newsletter"
    PODCAST = "podcast"


class NodeKind(str, Enum):
    ARTIFACT = "artifact"
    PERSON = "person"
    CONCEPT = "concept"


class EdgeKind(str, Enum):
    """NIL dimensions, plus structural edges.

    SHARED_LANGUAGE and TRUST are the two dimensions we ship at starter-pack
    fidelity. The other three are scaffolded for full-archive Phase 2.
    """

    # Structural
    AUTHORED_BY = "authored_by"        # Artifact -> Person
    APPEARS_IN = "appears_in"          # Concept -> Artifact

    # NIL dimensions
    SHARED_LANGUAGE = "shared_language"      # Concept <-> Concept (co-occurrence)
    TRUST = "trust"                          # Person -> Person (vouches, citations)
    INFORMAL_INFLUENCE = "informal_influence"  # Phase 2
    PSYCHOLOGICAL_SAFETY = "psychological_safety"  # Phase 2
    SIGNAL_FLOW = "signal_flow"              # Phase 2


class Artifact(BaseModel):
    id: str
    title: str
    filename: str
    type: ArtifactType
    date: str | None = None
    word_count: int | None = None
    tags: list[str] = Field(default_factory=list)
    guest: str | None = None  # podcasts only
    subtitle: str | None = None  # newsletters only
    source_url: str | None = None


class Concept(BaseModel):
    """A framework, principle, or named pattern surfaced from one or more artifacts.

    `canonical_name` is what we render. `aliases` lets us collapse near-duplicates
    that refer to the same idea (e.g., "JTBD" and "Jobs to be Done").
    """

    id: str
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)
    kind: str  # "framework" | "principle" | "metric" | "metaphor"
    one_line: str  # A grounded one-line description we can show on hover.


class ConceptMention(BaseModel):
    """One observed use of a concept inside one artifact."""

    concept_id: str
    artifact_id: str
    quote: str  # Short quoted phrase that grounds the mention.


class TrustEdge(BaseModel):
    """A person publicly endorsing, citing, or recommending another person.

    Source is the speaker. Target is who they vouched for.
    """

    source_person: str
    target_person: str
    artifact_id: str
    quote: str


class GraphNode(BaseModel):
    id: str
    label: str
    kind: NodeKind
    meta: dict = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    kind: EdgeKind
    weight: float = 1.0
    meta: dict = Field(default_factory=dict)


class Graph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    generated_at: str
    source: str  # "starter-pack" | "full-archive"
