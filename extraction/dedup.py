"""Post-processing dedup pass on graph.json.

Normalizes concept labels, merges near-duplicates, and rewrites the graph.

Usage:
  python -m extraction.dedup --graph app/data/graph.json
  python -m extraction.dedup --graph app/data/graph.json --dry-run

Strategy:
  1. Exact match after normalization (lowercase, strip punctuation, singularize).
  2. Known acronym/expansion pairs from a hand-curated map.
  3. Substring containment for short-form vs long-form (e.g. "RAG" in "Retrieval Augmented Generation").
  4. Edit-distance merge for very close labels (Levenshtein < 3 on labels longer than 8 chars).

For each merge group, the node with the most edges wins and becomes canonical.
All edges pointing at losing nodes are redirected to the winner.
Losing node's label is added to the winner's aliases list.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import defaultdict
from pathlib import Path

log = logging.getLogger("dedup")

# Hand-curated acronym expansions. Key = normalized acronym, value = normalized expansion.
_ACRONYMS: dict[str, str] = {
    "rlhf": "reinforcement learning from human feedback",
    "rag": "retrieval augmented generation",
    "jtbd": "jobs to be done",
    "gtm": "go to market",
    "ltv": "lifetime value",
    "cac": "customer acquisition cost",
    "nps": "net promoter score",
    "arr": "annual recurring revenue",
    "mrr": "monthly recurring revenue",
    "plg": "product led growth",
    "slg": "sales led growth",
    "dau": "daily active users",
    "mau": "monthly active users",
    "aeo": "answer engine optimization",
    "seo": "search engine optimization",
    "kpi": "key performance indicator",
    "okr": "objectives and key results",
    "llm": "large language model",
    "mcp": "model context protocol",
    "api": "application programming interface",
    "b2b": "business to business",
    "b2c": "business to consumer",
}


def _normalize(label: str) -> str:
    """Normalize a concept label for comparison."""
    s = label.lower().strip()
    # strip possessives
    s = re.sub(r"'s\b", "", s)
    # replace hyphens and underscores with spaces
    s = s.replace("-", " ").replace("_", " ")
    # remove remaining non-alphanumeric except spaces
    s = re.sub(r"[^\w\s]", " ", s)
    # collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    # simple singularization: trailing 's' on words > 4 chars
    words = s.split()
    depl = []
    for w in words:
        if w.endswith("ies") and len(w) > 5:
            depl.append(w[:-3] + "y")
        elif w.endswith("es") and len(w) > 5:
            depl.append(w[:-2])
        elif w.endswith("s") and not w.endswith("ss") and len(w) > 4:
            depl.append(w[:-1])
        else:
            depl.append(w)
    return " ".join(depl)


def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


def _build_degree(nodes: list[dict], edges: list[dict]) -> dict[str, int]:
    degree: dict[str, int] = defaultdict(int)
    for e in edges:
        degree[e["source"]] += 1
        degree[e["target"]] += 1
    return degree


def _find_merge_groups(concept_nodes: list[dict], degree: dict[str, int]) -> list[list[str]]:
    """Return groups of node ids that should be merged together."""
    ids = [n["id"] for n in concept_nodes]
    label_by_id = {n["id"]: n["label"] for n in concept_nodes}
    norm_by_id = {n["id"]: _normalize(n["label"]) for n in concept_nodes}

    # union-find
    parent: dict[str, str] = {nid: nid for nid in ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        # keep the higher-degree node as root
        if degree.get(ra, 0) >= degree.get(rb, 0):
            parent[rb] = ra
        else:
            parent[ra] = rb

    # 1. Exact normalized match
    by_norm: dict[str, list[str]] = defaultdict(list)
    for nid in ids:
        by_norm[norm_by_id[nid]].append(nid)
    for group in by_norm.values():
        for nid in group[1:]:
            union(group[0], nid)

    # 2. Acronym expansion matches
    norm_to_id = {norm_by_id[nid]: nid for nid in ids}
    for acronym, expansion in _ACRONYMS.items():
        if acronym in norm_to_id and expansion in norm_to_id:
            union(norm_to_id[acronym], norm_to_id[expansion])

    # 3. Substring containment: short label (≤ 5 chars) contained in longer label's normalized form
    #    e.g. "RAG" inside "Retrieval Augmented Generation"
    short_ids = [nid for nid in ids if len(label_by_id[nid]) <= 5]
    for sid in short_ids:
        short_norm = norm_by_id[sid]
        for nid in ids:
            if nid == sid:
                continue
            if short_norm in norm_by_id[nid].split():
                union(sid, nid)

    # 4. Edit distance < 3 for labels longer than 10 chars
    long_ids = [nid for nid in ids if len(label_by_id[nid]) > 10]
    for i in range(len(long_ids)):
        for j in range(i + 1, len(long_ids)):
            a, b = long_ids[i], long_ids[j]
            na, nb = norm_by_id[a], norm_by_id[b]
            if abs(len(na) - len(nb)) > 4:
                continue  # fast skip
            if _levenshtein(na, nb) < 3:
                union(a, b)

    # Collect groups
    groups: dict[str, list[str]] = defaultdict(list)
    for nid in ids:
        groups[find(nid)].append(nid)
    return [g for g in groups.values() if len(g) > 1]


def dedup_graph(graph: dict, dry_run: bool = False) -> tuple[dict, int]:
    """Return cleaned graph and merge count."""
    nodes: list[dict] = graph["nodes"]
    edges: list[dict] = graph["edges"]

    degree = _build_degree(nodes, edges)
    concept_nodes = [n for n in nodes if n.get("kind") == "concept"]
    other_nodes = [n for n in nodes if n.get("kind") != "concept"]

    groups = _find_merge_groups(concept_nodes, degree)
    log.info("Found %d merge groups across %d concepts", len(groups), len(concept_nodes))

    # Build redirect map: loser_id -> winner_id
    redirect: dict[str, str] = {}
    node_by_id = {n["id"]: n for n in concept_nodes}

    merged_count = 0
    for group in groups:
        # Winner = highest degree
        winner_id = max(group, key=lambda nid: degree.get(nid, 0))
        losers = [nid for nid in group if nid != winner_id]
        winner = node_by_id[winner_id]

        # Merge aliases
        aliases = list(winner.get("meta", {}).get("aliases", []))
        for loser_id in losers:
            loser = node_by_id[loser_id]
            aliases.append(loser["label"])
            aliases.extend(loser.get("meta", {}).get("aliases", []))
            redirect[loser_id] = winner_id
            log.info("  Merge: %r -> %r", loser["label"], winner["label"])
            merged_count += 1

        winner.setdefault("meta", {})["aliases"] = sorted(set(aliases))

    if dry_run:
        log.info("Dry run — not writing. Would merge %d nodes.", merged_count)
        return graph, merged_count

    # Remap edges
    new_edges = []
    seen_pairs: set[tuple] = set()
    for e in edges:
        src = redirect.get(e["source"], e["source"])
        tgt = redirect.get(e["target"], e["target"])
        if src == tgt:
            continue  # self-loop after merge
        key = (src, tgt, e["kind"])
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        new_edges.append({**e, "source": src, "target": tgt})

    # Keep only winner concept nodes + all others
    loser_ids = set(redirect.keys())
    new_nodes = [n for n in concept_nodes if n["id"] not in loser_ids] + other_nodes

    graph["nodes"] = new_nodes
    graph["edges"] = new_edges
    return graph, merged_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, default=Path("app/data/graph.json"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    graph = json.loads(args.graph.read_text())
    before_nodes = len(graph["nodes"])
    before_edges = len(graph["edges"])

    graph, merged = dedup_graph(graph, dry_run=args.dry_run)

    after_nodes = len(graph["nodes"])
    after_edges = len(graph["edges"])
    log.info(
        "Nodes: %d -> %d (-%d merged), Edges: %d -> %d",
        before_nodes, after_nodes, merged, before_edges, after_edges,
    )

    if not args.dry_run:
        args.graph.write_text(json.dumps(graph, indent=2))
        log.info("Wrote %s", args.graph)


if __name__ == "__main__":
    main()
