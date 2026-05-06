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
})();
