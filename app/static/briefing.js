// Briefing surface frontend.
//
// Posts a pasted external artifact to /api/briefing and renders the structured
// briefing: summary, priorities (each with corpus agreement and pushback), and
// questions to ask. Falls back gracefully when the backend is in stub mode.

(function () {
  const form = document.getElementById("briefing-form");
  const textarea = document.getElementById("artifact");
  const submit = document.getElementById("briefing-submit");
  const status = document.getElementById("briefing-status");
  const response = document.getElementById("briefing-response");

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

  function renderEvidence(entry, lane) {
    const artifactTitle = entry.artifact_id ? nodeLabel(entry.artifact_id) : "";
    const showSource = artifactTitle && artifactTitle !== entry.artifact_id;
    return `<article class="evidence evidence-${lane}">
      <header>
        <strong>${escapeHtml(entry.speaker || "")}</strong>
      </header>
      ${showSource ? `<p class="take-source muted">${escapeHtml(artifactTitle)}</p>` : ""}
      ${entry.quote ? `<blockquote>${escapeHtml(entry.quote)}</blockquote>` : ""}
      ${entry.why ? `<p class="evidence-why">${escapeHtml(entry.why)}</p>` : ""}
    </article>`;
  }

  function renderPriority(p, idx) {
    const agrees = (p.agrees || []).map((e) => renderEvidence(e, "agree")).join("");
    const pushes = (p.pushes_back || []).map((e) => renderEvidence(e, "push")).join("");
    return `<section class="priority">
      <header class="priority-header">
        <span class="priority-index">${idx + 1}</span>
        <h4>${escapeHtml(p.priority || "")}</h4>
      </header>
      ${
        p.evidence_quote
          ? `<blockquote class="priority-evidence">${escapeHtml(p.evidence_quote)}</blockquote>`
          : ""
      }
      <div class="priority-lanes">
        <div class="lane lane-agree">
          <h5>Where the corpus agrees</h5>
          ${agrees || `<p class="muted lane-empty">No direct support in the graph.</p>`}
        </div>
        <div class="lane lane-push">
          <h5>Where the corpus pushes back</h5>
          ${pushes || `<p class="muted lane-empty">No direct pushback in the graph.</p>`}
        </div>
      </div>
    </section>`;
  }

  function render(result) {
    const stubBanner = result.stub
      ? `<div class="stub-banner">Stub mode. Set <code>ANTHROPIC_API_KEY</code> and restart the server for a real briefing.</div>`
      : "";

    const errorBanner = result.error
      ? `<div class="error-banner"><strong>Briefing failed:</strong> ${escapeHtml(result.error.kind)}<pre class="error-detail">${escapeHtml(result.error.detail || "")}</pre></div>`
      : "";

    const priorities = (result.priorities || []).map(renderPriority).join("");
    const questions = (result.questions_to_ask || [])
      .map((q) => `<li>${escapeHtml(q)}</li>`)
      .join("");

    response.innerHTML = `
      ${errorBanner}
      ${stubBanner}
      ${
        result.summary
          ? `<section class="lookup-section"><h3>Summary</h3><p>${escapeHtml(result.summary)}</p></section>`
          : ""
      }
      ${
        priorities
          ? `<section class="lookup-section"><h3>Priorities</h3><div class="priorities">${priorities}</div></section>`
          : ""
      }
      ${
        questions
          ? `<section class="lookup-section"><h3>Questions to ask</h3><ul class="questions">${questions}</ul></section>`
          : ""
      }
    `.trim();
  }

  function setBusy(busy) {
    submit.disabled = busy;
    submit.textContent = busy ? "Reading..." : "Read it";
    status.textContent = busy ? "Reading the artifact against the graph. Usually 10 to 25 seconds." : "";
  }

  const REQUEST_TIMEOUT_MS = 60000;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const artifact = textarea.value.trim();
    if (!artifact) return;

    setBusy(true);
    response.innerHTML = "";

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const res = await fetch("/api/briefing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ artifact }),
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
      response.innerHTML = `<p class="error">Briefing failed: ${escapeHtml(msg)}</p>`;
    } finally {
      clearTimeout(timeoutId);
      setBusy(false);
    }
  });
})();
