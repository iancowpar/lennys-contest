# Adjacent prompts review

Same lens as the Briefing prompt iteration. Diagnostic only — no edits proposed unless we want to make them.

## `prompts/lookup.txt` (runtime)

Most likely to benefit from the same pre-promotion checklist treatment as `briefing.txt` after `10066de`.

**Structural risks:**

1. **Flat rule list, same failure mode as pre-`10066de` briefing.** "Pick at most three matched concepts," "two speakers who genuinely disagree," and the verbatim-quote rule are all peers in a list. The model is likely treating them as soft preferences. Move the disagreement and verbatim rules into an explicit pre-promotion check.
2. **No "broadening" guard on contrasting takes.** Same bug we saw in Briefing's `pushes_back`: the `position` sentence can paraphrase the corpus quote's subject to manufacture disagreement. The "two speakers who genuinely disagree, not two who agree from different angles" rule names the failure but doesn't give the model a mechanical test. Borrow the briefing checklist item: "the `position` introduces no noun the corpus quote did not contain."
3. **No frame-import constraint.** A situation that doesn't mention AI/platform/moat could still trigger a draft_move that imports those frames. Same drift we caught in Briefing's iteration 2.
4. **No length cap on `quote`.** Briefing now requires evidence_quote ≤15 words. Lookup has no equivalent for the corpus quote it cites. Long quotes break the take cards visually and dilute signal.
5. **Banned-phrase list is shorter than Briefing's.** Missing "it is worth noting." Probably fine but worth aligning.

**What's already strong:**
- The fallback ("no real counterposition in the graph" entry) is well-specified and matches the briefing approach for empty `pushes_back`.
- `draft_move` instructions are concrete: two-three sentences, paste-able, active voice, no throat-clearing. Good model of how to constrain a generative field.
- `political_capital_tradeoff` instruction names what's at stake on both sides. Borrow this framing for a future Briefing field if it ever grows one.

**Likely impact of porting the checklist:** medium. Lookup's failure modes are subtler than Briefing's because the situation input is usually more specific than a JD's responsibility list, so the duplicated-bullet failure mode doesn't apply. The broadening test on contrasting takes is the highest-value port.

## `prompts/shared_language.txt` (offline)

Lower-priority because it runs offline and the output ships in `app/data/graph.json` — failures show up at extraction time, not at user runtime.

**Structural risks:**

1. **No frequency or distinctiveness threshold.** A concept mentioned once in passing can land in the graph next to one referenced across multiple artifacts. The "What does NOT count" list filters genericity but not single-use coinages that aren't really shared language. Consider: "a concept must be used by the speaker as if the listener already knows it (no full re-explanation), OR appear with the same canonical phrasing twice."
2. **`one_line` rule is good but unenforced.** "no business-school filler" is the right intent; no examples of bad filler. Adding 2-3 reject examples would tighten it.
3. **Quote cap is in place** (under 20 words). ✓

**What's already strong:**
- "What does NOT count" examples are sharp. The "generic business words" reject list is the right shape.
- "Bias toward precision over recall. A short, sharp list is better than a long, soft one." — same posture as the Briefing checklist preamble.
- The `kind` enum (framework / principle / metric / metaphor) is small and unambiguous.

## `prompts/trust_signals.txt` (offline)

Lowest-priority same reason as shared_language. Already in good shape.

**Structural risks:**

1. **Relationship enum is subjective.** "endorses" vs "credits" vs "learned_from" can collapse into each other. The current rules don't disambiguate. Either add a one-line tie-breaker per relationship, or collapse to fewer types.
2. **No source-person ambiguity guard.** "use the `speaker_name` field provided in the input metadata if it is present; otherwise infer from context" — the inference fallback is a hallucination risk. Worth either erroring out on missing speaker_name or returning an explicit "unknown" source.

**What's already strong:**
- Tight "what counts" / "what doesn't" with concrete reject examples (Steve Jobs in passing, neutral peer mentions).
- Quote cap (under 25 words). ✓
- "Be precise. Two strong edges beat ten weak ones." — consistent posture across the prompt suite.

## Cross-cutting observations

- All four prompts use the same **"two strong > many weak"** posture. That's a deliberate house style and worth preserving.
- All four require **verbatim quotes** from the source. The Briefing harness can verify this mechanically; the others have no automated check. If the offline extraction grows enough that we care, a similar harness against `data/extracted/*.jsonl` would catch invented quotes early.
- Only `briefing.txt` has the **frame-import constraint**. If `lookup.txt` shows the same drift in production, port it.
- The Lookup and Briefing prompts both use the same `<graph>` block convention. The graph projection itself (in `app/lookup.py:graph_context`) is the load-bearing structure both prompts rely on. Worth versioning explicitly if the projection ever changes shape.
