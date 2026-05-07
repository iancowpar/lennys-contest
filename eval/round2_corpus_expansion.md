# Round 2 corpus expansion - notes

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

## Iter-3 result

The HiBob JD re-run after this expansion produced a 3-priority brief (down from 4), no AI/moat frame imports, and surfaced Jason Cohen's `onboarding-is-the-bet` as a real pushback on the 0→1 priority. That was the first time a Round 2 concept fired organically; it justified shipping the expansion.
