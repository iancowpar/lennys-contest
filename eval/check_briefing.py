"""Programmatic checks for the briefing prompt's output.

Runs a fixture artifact through the briefing endpoint (in-process) and
asserts the rules in prompts/briefing.txt that are mechanically checkable:

- evidence_quote is verbatim from the artifact
- evidence_quote is 15 words or fewer
- evidence_quote is not a duplicated bullet (does not appear more than once
  in the artifact)
- agree/pushback quotes are verbatim from the graph
- the model does not import frame words (AI, platform, ecosystem, moat) the
  artifact itself never uses
- 4 priorities cap
- 0-2 entries per agrees/pushes_back
- 3-5 questions_to_ask
- no em dashes anywhere in the response
- none of the banned phrases

Usage:
  # Generate a fresh briefing and check it
  python -m eval.check_briefing eval/fixtures/hibob_pm_payroll.txt

  # Check a pre-saved briefing JSON against an artifact (no model call)
  python -m eval.check_briefing eval/fixtures/hibob_pm_payroll.txt --brief path/to/brief.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.briefing import briefing  # noqa: E402
from app.lookup import graph_context  # noqa: E402

FRAME_WORDS = ["AI", "platform", "ecosystem", "moat"]
BANNED_PHRASES = [
    "in today's fast-paced world",
    "here's what i keep coming back to",
    "let me know your thoughts",
    "it is worth noting",
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _word_count(text: str) -> int:
    return len(text.split())


def _all_text_blobs(brief: dict) -> list[str]:
    blobs: list[str] = [brief.get("summary", "")]
    for p in brief.get("priorities", []):
        blobs.append(p.get("priority", ""))
        blobs.append(p.get("evidence_quote", ""))
        for entry in p.get("agrees", []) + p.get("pushes_back", []):
            blobs.append(entry.get("why", ""))
    blobs.extend(brief.get("questions_to_ask", []))
    return [b for b in blobs if b]


def _graph_quotes() -> set[str]:
    ctx = json.loads(graph_context())
    quotes: set[str] = set()
    for concept in ctx.get("concepts", []):
        for appearance in concept.get("appearances", []):
            q = appearance.get("quote")
            if q:
                quotes.add(_normalize(q))
    return quotes


def run_checks(artifact: str, brief: dict) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []  # (severity, message)

    if brief.get("stub"):
        findings.append(("warn", "Response is from the stub (ANTHROPIC_API_KEY not set or SDK missing)."))
        return findings

    if brief.get("error"):
        err = brief["error"]
        findings.append(("warn", f"Response is an error ({err.get('kind')}): {err.get('detail', '')[:200]}"))
        return findings

    artifact_norm = _normalize(artifact)
    graph_quotes = _graph_quotes()
    priorities = brief.get("priorities", [])

    if len(priorities) > 4:
        findings.append(("fail", f"priorities count {len(priorities)} > 4"))

    questions = brief.get("questions_to_ask", [])
    if not (3 <= len(questions) <= 5):
        findings.append(("fail", f"questions_to_ask count {len(questions)} not in [3,5]"))

    for i, p in enumerate(priorities, 1):
        eq = p.get("evidence_quote", "")
        eq_norm = _normalize(eq)

        if _word_count(eq) > 15:
            findings.append(("fail", f"P{i} evidence_quote is {_word_count(eq)} words (>15): {eq!r}"))

        if eq_norm and eq_norm not in artifact_norm:
            findings.append(("fail", f"P{i} evidence_quote is not verbatim in the artifact: {eq!r}"))

        if eq_norm and artifact_norm.count(eq_norm) > 1:
            findings.append((
                "fail",
                f"P{i} evidence_quote appears {artifact_norm.count(eq_norm)} times in the artifact (duplicated bullet): {eq!r}",
            ))

        for tag in ("agrees", "pushes_back"):
            entries = p.get(tag, [])
            if len(entries) > 2:
                findings.append(("fail", f"P{i} {tag} has {len(entries)} entries (>2)"))
            for j, entry in enumerate(entries, 1):
                q = entry.get("quote", "")
                if q and _normalize(q) not in graph_quotes:
                    findings.append((
                        "fail",
                        f"P{i} {tag}[{j}] quote is not verbatim in the graph: {q!r}",
                    ))

    for word in FRAME_WORDS:
        in_artifact = re.search(rf"\b{re.escape(word)}\b", artifact, re.IGNORECASE) is not None
        if in_artifact:
            continue
        for blob in _all_text_blobs(brief):
            if re.search(rf"\b{re.escape(word)}\b", blob, re.IGNORECASE):
                findings.append((
                    "fail",
                    f"frame word {word!r} appears in output but not in the artifact",
                ))
                break

    for blob in _all_text_blobs(brief):
        if "—" in blob:
            findings.append(("fail", f"em dash in output: {blob[:80]!r}"))
            break

    for blob in _all_text_blobs(brief):
        b_low = blob.lower()
        for phrase in BANNED_PHRASES:
            if phrase in b_low:
                findings.append(("fail", f"banned phrase {phrase!r} in output"))

    return findings


def main() -> int:
    args = sys.argv[1:]
    if len(args) not in (1, 3) or (len(args) == 3 and args[1] != "--brief"):
        print("usage: python -m eval.check_briefing <artifact_path> [--brief <brief.json>]", file=sys.stderr)
        return 2

    artifact_path = Path(args[0])
    artifact = artifact_path.read_text()

    if len(args) == 3:
        brief = json.loads(Path(args[2]).read_text())
    else:
        brief = briefing(artifact)
    findings = run_checks(artifact, brief)

    fails = [m for sev, m in findings if sev == "fail"]
    warns = [m for sev, m in findings if sev == "warn"]

    print(f"--- briefing for {artifact_path.name} ---")
    print(json.dumps(brief, indent=2))
    print()
    print(f"--- checks: {len(fails)} fail, {len(warns)} warn ---")
    for w in warns:
        print(f"  WARN: {w}")
    for f in fails:
        print(f"  FAIL: {f}")

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
