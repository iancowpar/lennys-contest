// Lookup surface frontend.
//
// Posts the user's situation to /api/lookup and renders the structured
// response. Falls back gracefully when the backend is in stub mode (no
// ANTHROPIC_API_KEY) by surfacing the stub flag in the UI.

(function () {
  const form = document.getElementById("lookup-form");
  const textarea = document.getElementById("situation");
  const submit = document.getElementById("lookup-submit");
  const status = document.getElementById("lookup-status");
  const response = document.getElementById("lookup-response");

  if (!form) return;

  function escapeHtml(value) {
    if (value == null) return "";
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function nodeLabel(id) {
    if (!window.fullGraph) return id;
    const n = window.fullGraph.nodes.find((node) => node.id === id);
    return n ? n.label : id;
  }

  function renderConcept(c) {
    const label = nodeLabel(c.concept_id);
    return `<li>
      <span class="concept-pill">${escapeHtml(label)}</span>
      <span class="concept-why">${escapeHtml(c.why_it_applies || "")}</span>
    </li>`;
  }

  function renderTake(t) {
    return `<article class="take">
      <header>
        <strong>${escapeHtml(t.speaker || "")}</strong>
        <span class="muted">${escapeHtml(t.artifact_id || "")}</span>
      </header>
      <p class="position">${escapeHtml(t.position || "")}</p>
      ${t.quote ? `<blockquote>${escapeHtml(t.quote)}</blockquote>` : ""}
    </article>`;
  }

  function render(result) {
    const stubBanner = result.stub
      ? `<div class="stub-banner">Stub mode. Add <code>ANTHROPIC_API_KEY</code> in Replit secrets and restart the workflow for a real read.</div>`
      : "";

    const concepts = (result.matched_concepts || []).map(renderConcept).join("");
    const takes = (result.contrasting_takes || []).map(renderTake).join("");

    response.innerHTML = `
      ${stubBanner}
      ${
        concepts
          ? `<section class="lookup-section"><h3>What's at play</h3><ul class="concepts">${concepts}</ul></section>`
          : ""
      }
      ${
        takes
          ? `<section class="lookup-section"><h3>Two takes</h3><div class="takes">${takes}</div></section>`
          : ""
      }
      ${
        result.political_capital_tradeoff
          ? `<section class="lookup-section"><h3>Political capital</h3><p>${escapeHtml(result.political_capital_tradeoff)}</p></section>`
          : ""
      }
      ${
        result.draft_move
          ? `<section class="lookup-section"><h3>Draft move</h3><blockquote class="draft">${escapeHtml(result.draft_move)}</blockquote></section>`
          : ""
      }
    `.trim();
  }

  function setBusy(busy) {
    submit.disabled = busy;
    submit.textContent = busy ? "Reading..." : "Read it";
    status.textContent = busy ? "Thinking. This usually takes 5 to 15 seconds." : "";
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const situation = textarea.value.trim();
    if (!situation) return;

    setBusy(true);
    response.innerHTML = "";

    try {
      const res = await fetch("/api/lookup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ situation }),
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`HTTP ${res.status}: ${detail.slice(0, 200)}`);
      }
      const data = await res.json();
      render(data);
    } catch (err) {
      response.innerHTML = `<p class="error">Lookup failed: ${escapeHtml(err.message)}</p>`;
    } finally {
      setBusy(false);
    }
  });
})();
