# Round 2 corpus expansion - review before commit

Staged but **not committed**. Review the diff and decide whether to ship.

## What changed

- `extraction/seed.py`: +8 artifacts, +18 concepts, +18 mentions, +3 trust edges. Source string: `seed:starter-pack-curated-20` → `seed:starter-pack-curated-28`.
- `app/data/graph.json`: regenerated via `python -m extraction.seed`. 80→116 nodes, 170→209 edges.
- `CLAUDE.md`: added graph stats and a note that the LLM extraction pipeline has never been run end-to-end (the shipped graph is hand-curated from `seed.py`).

## Why these 8

The existing 31 concepts skewed heavily AI/evals/PMF — that's what was leaking the "AI-native or platform-level thinking" frame into the iter-2 HiBob brief. The 8 new artifacts intentionally bias toward classic SaaS, hiring, pricing, sales, and influence. Each anchors on distinctive verbatim phrasing.

| Artifact | Guest | Why |
|---|---|---|
| `eoghan-mccabe` | Eoghan McCabe (Intercom) | Pricing recovery story; `outcome-based-pricing`, `beautifully-simple-pricing` |
| `jason-cohen-stalled-growth` | Jason Cohen | Classic stalled-growth playbook; `prices-too-low`, `onboarding-is-the-bet` |
| `grant-lee` | Grant Lee (Gamma) | $100M ARR story; `first-30-seconds`, `hire-painfully-slowly` |
| `brian-halligan` | Brian Halligan (HubSpot) | Scaling pitfalls; `kids-and-adults-table`, `blind-references`, `hire-slow-fire-fast` |
| `keith-rabois` | Keith Rabois | Hiring prism; `value-creation-vs-preservation`, `ceo-counterfactual-question` |
| `matt-macinnis` | Matt MacInnis (Rippling) | Interview tactics; `same-case-study-rubric` |
| `jason-lemkin` | Jason Lemkin (SaaStr) | B2B sales; `founder-time-budget`, `pirates-and-romantics`, `first-ten-determine-dna` |
| `jessica-fain` | Jessica Fain (Webflow) | Influence skill; `forget-the-skills-with-execs`, `executive-calendar-as-stream` |

Several of these pair with concepts the corpus already has. The Rippling episode (`matt-macinnis`) is especially relevant because Rippling shows up by name in the HiBob JD's competitor list (Q4 of the iter-2 output asked about Rippling specifically).

## Quality bar

Every quote in the new mentions is **verbatim** from the source as pulled via the Lenny archive MCP. No paraphrasing. Quotes were extracted via `read_excerpt` calls; verifiable by re-running the same calls. Concept `one_line` descriptions were written by me and follow the existing seed.py voice.

## Known limitation: speaker attribution

The existing graph attributes every quote to the artifact's primary `guest`, even when Lenny actually said the words (the `authored_by` edge is the artifact author, used as the speaker for all quotes from that artifact). Two of the new mentions are technically Lenny's words inside a guest's episode:

- `eoghan-mccabe`: `"beautifully simple pricing is where you want to get to"` is Lenny paraphrasing Madhavan, attributed to Eoghan.
- `brian-halligan`: `"the adults are spending half their time just recruiting and interviewing"` is Brian's, no issue here.

This matches the existing pattern in seed.py (e.g., the cat-wu artifact's intro quotes). If you care, the quick fix is per-quote speaker; the bigger fix is a `quoted_by` edge type.

## Reversal

If something feels off:

```bash
git checkout extraction/seed.py app/data/graph.json CLAUDE.md
```

That restores the 20-artifact graph with no other side effects. The eval harness, the prompt edits, and the LLM error surfacing all stay.

## What I'd do next

1. Spot-check 2-3 of the new entries by clicking through Atlas in the running app to confirm the nodes and edges render.
2. Re-run the HiBob JD through the Briefing tab to see if the richer corpus + iter-3 prompt produce a sharper output. Predictions:
   - `forget-the-skills-with-execs` (Jessica) likely shows up as agree on any "leadership/influence" priority.
   - `pirates-and-romantics` (Lemkin) might pushback on a JD that asks for "process-rigor" PMs.
   - `value-creation-vs-preservation` (Rabois) is a strong candidate for any JD that hedges on "experience required."
3. If happy, commit `extraction/seed.py`, `app/data/graph.json`, and `CLAUDE.md` together. Suggested message:

   ```
   Expand graph from 20 to 28 artifacts; bias toward non-AI corners

   Adds Eoghan McCabe (pricing), Jason Cohen (stalled growth), Grant Lee
   (Gamma), Brian Halligan (HubSpot scaling), Keith Rabois (hiring),
   Matt MacInnis (Rippling interview tactics), Jason Lemkin (SaaStr sales),
   Jessica Fain (executive influence). 18 new concepts, 18 new mentions,
   3 new trust edges. Source: seed:starter-pack-curated-28. Filling the
   non-AI gap surfaced by the iter-2 HiBob brief, where the model imported
   AI/moat frames the artifact never used.
   ```
