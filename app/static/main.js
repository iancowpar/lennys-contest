// Surface switching between Atlas (graph) and Lookup (situation read).
//
// graph.js owns the Atlas. lookup.js owns the Lookup. This file just toggles
// which one is visible and re-fits the graph when Atlas comes back into view
// so vis-network does not render off-canvas after a hidden -> visible swap.

(function () {
  const buttons = document.querySelectorAll("nav#surfaces button");
  const surfaces = document.querySelectorAll("section.surface");
  const filters = document.getElementById("filters");

  function show(surfaceName) {
    surfaces.forEach((s) => {
      s.classList.toggle("active", s.id === `${surfaceName}-surface`);
    });
    buttons.forEach((b) => {
      b.classList.toggle("active", b.dataset.surface === surfaceName);
    });
    if (filters) {
      filters.style.display = surfaceName === "atlas" ? "" : "none";
    }
    if (surfaceName === "atlas" && window.btoFitGraph) {
      // Give the layout a tick to settle before fitting, otherwise the
      // canvas dimensions can still report zero from the just-shown div.
      setTimeout(() => window.btoFitGraph(), 50);
    }
  }

  buttons.forEach((b) => {
    b.addEventListener("click", () => show(b.dataset.surface));
  });

  // Guide CTA buttons (detail panel empty state) — switch surface + load sample.
  document.querySelectorAll(".guide-cta[data-goto]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.goto;
      show(target);
      // Auto-load the first sample chip on the target surface so the user
      // lands with content already in the textarea, not another empty state.
      const firstChip = document.querySelector(
        `#${target}-surface .sample-btn`
      );
      if (firstChip) firstChip.click();
    });
  });

  // Sample-artifact buttons. Fetch the bundled sample text and drop it into
  // the matching textarea so first-time visitors do not have to paste 16KB
  // of content to try the surface.
  document.querySelectorAll(".sample-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const sample = btn.dataset.sample;
      const targetId = btn.dataset.target;
      const target = document.getElementById(targetId);
      if (!sample || !target) return;
      const original = btn.textContent;
      btn.disabled = true;
      btn.textContent = "Loading sample...";
      try {
        const res = await fetch(sample);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        target.value = (await res.text()).trim();
        target.focus();
      } catch (err) {
        btn.textContent = `Sample failed: ${err.message}`;
        setTimeout(() => { btn.textContent = original; btn.disabled = false; }, 3000);
        return;
      }
      btn.textContent = original;
      btn.disabled = false;
    });
  });
})();
