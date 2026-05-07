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
    const artifactTitle = t.artifact_id ? nodeLabel(t.artifact_id) : "";
    const showSource = artifactTitle && artifactTitle !== t.artifact_id;
    return `<article class="take">
      <header>
        <strong>${escapeHtml(t.speaker || "")}</strong>
      </header>
      ${showSource ? `<p class="take-source muted">${escapeHtml(artifactTitle)}</p>` : ""}
      <p class="position">${escapeHtml(t.position || "")}</p>
      ${t.quote ? `<blockquote>${escapeHtml(t.quote)}</blockquote>` : ""}
    </article>`;
  }

  function render(result) {
    const stubBanner = result.stub
      ? `<div class="stub-banner">Stub mode. Set <code>ANTHROPIC_API_KEY</code> and restart the server for a real read.</div>`
      : "";

    const errorBanner = result.error
      ? `<div class="error-banner"><strong>Lookup failed:</strong> ${escapeHtml(result.error.kind)}<pre class="error-detail">${escapeHtml(result.error.detail || "")}</pre></div>`
      : "";

    const concepts = (result.matched_concepts || []).map(renderConcept).join("");
    const takes = (result.contrasting_takes || []).map(renderTake).join("");

    response.innerHTML = `
      ${errorBanner}
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

  const REQUEST_TIMEOUT_MS = 60000;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const situation = textarea.value.trim();
    if (!situation) return;

    setBusy(true);
    response.innerHTML = "";

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const res = await fetch("/api/lookup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ situation }),
        signal: controller.signal,
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`HTTP ${res.status}: ${detail.slice(0, 200)}`);
      }
      const data = await res.json();
      render(data);
    } catch (err) {
      const msg = err.name === "AbortError"
        ? `Request timed out after ${REQUEST_TIMEOUT_MS / 1000} seconds.`
        : err.message;
      response.innerHTML = `<p class="error">Lookup failed: ${escapeHtml(msg)}</p>`;
    } finally {
      clearTimeout(timeoutId);
      setBusy(false);
    }
  });
})();
