# Briefing surface: edge-case audit

Punch list, not fixes. Ranked by user-visible impact.

## High

1. ~~Silent stub fallback on malformed JSON.~~ **FIXED.** `app/briefing.py` and `app/lookup.py` now raise `LLMError("invalid_json", ...)` when the model returns non-JSON. The public `briefing()` / `lookup()` functions catch `LLMError` and return a structured error response with `result.error.{kind, detail}`. Frontend renders an error banner via `.error-banner` (`app/static/style.css`).

2. ~~Silent stub fallback on Anthropic exception.~~ **FIXED.** Same change. `LLMError("anthropic_error", str(exc)[:300])` is raised and surfaced to the frontend.

3. ~~No request timeout.~~ **FIXED.** `app/static/briefing.js` and `app/static/lookup.js` now wrap `fetch` with a 60s `AbortController`. `AbortError` renders as "Request timed out after 60 seconds."

4. **`fullGraph` race in `nodeLabel`.** `app/static/briefing.js:27` reads `window.fullGraph`, which is populated by `graph.js` after an async fetch. If the user clicks Briefing first and submits before Atlas loads, evidence cards lose the artifact title (fall through to id-as-label). In practice the graph fetch resolves in <500ms on init and the user has to paste a long artifact first, so this is rare. Defer until it actually shows up. Fix path: preload the graph on app start, or `await` it inside `nodeLabel`.

## Medium

5. ~~Code-fence stripping is fragile.~~ **FIXED.** Replaced the `text.strip("`")` shim with `extract_json_object()` in `app/lookup.py`, used by both surfaces. Handles fenced (with or without `json` tag), prose-wrapped fenced, prose-wrapped bare object, and naked JSON.

6. **No retry on transient Anthropic errors.** Single attempt, then stub. A simple one-shot retry on `RateLimitError` and `APIConnectionError` would absorb most flakes.

7. **Empty-state handling is implicit.** When `priorities: []` (the rule for thin artifacts), the Priorities section just disappears via the `priorities ? ... : ""` ternary in `briefing.js:88-92`. Same for empty `summary` or `questions_to_ask`. Nothing tells the user "this artifact was too thin." Render the summary even when priorities are empty, since the prompt instructs the model to put the explanation there.

8. **Long evidence quotes.** Now that the prompt caps `evidence_quote` at 15 words, this is mostly moot — but if the model violates the cap, the blockquote in `priority-evidence` will wrap into a tall block. Worth checking the CSS handles a 200-word quote without breaking the lane layout.

## Low

9. **`maxlength=16000` is silent.** The textarea silently truncates pasted content over 16k chars. A small character counter or a "truncated" hint would be friendlier.

10. **Repeated speakers across agree/pushback** (e.g. Singhal on both sides for the same priority) render two near-identical cards. Visually noisy. Could collapse the speaker header when the same speaker appears in both lanes for the same priority. Cosmetic.

11. **No copy-to-clipboard on the rendered brief.** Friction if you want to send the read to someone. Feature, not a bug.

12. **Stub banner copy.** `briefing.js:73` says "restart the workflow" — Replit-specific phrasing. Fine for the contest demo, but if the surface ever runs outside Replit it's wrong.

## Not bugs, but worth knowing

- The `briefing` and `lookup` system prompts are no longer cached in-process (commit `10066de`'s follow-up — lru_cache removed). Edits to `prompts/*.txt` land without a server restart. This was the silent staleness in the first round of prompt iteration.
- The harness in `eval/check_briefing.py` covers the mechanical rules (length, verbatim, duplicated bullet, frame imports, counts). It does NOT cover the semantic rules (whole-document hedging, signal-rich phrasing preference, broadening test for pushback "why" sentences). Those still need eyeballing.
