// Beneath the Org Chart - Atlas frontend
//
// Loads /api/graph, renders a force-directed network using vis-network.
// Features:
//   - Edge-kind filter buttons (Shared language / Trust / All)
//   - "Top themes" filter: only high-degree concept nodes + all people/artifacts
//   - Node sizing by degree (more connections = bigger/bolder)
//   - Label visibility threshold (low-degree nodes show label only on hover)
//   - Side-panel detail on click
//   - Real-time node search with autocomplete dropdown

const COLORS = {
  artifact: "#8b9eff",
  person: "#6ee7b7",
  concept: "#f3a712",
};

const EDGE_LABELS = {
  shared_language: "Shared language",
  trust: "Trust",
  authored_by: "Authored by",
  appears_in: "Appears in",
};

const ARTIFACT_LABEL_MAX = 48;

// Minimum shared_language degree for a concept to appear in the "Top themes" filter.
const TOP_THEMES_DEGREE = 15;
// Minimum degree to show a label at full opacity (below this the label is hidden unless hovered).
const LABEL_VISIBLE_DEGREE = 8;

function truncate(text, max) {
  if (!text || text.length <= max) return text;
  return text.slice(0, max - 1).trimEnd() + "…";
}

let fullGraph = null;
let network = null;
let currentDegree = {};   // nodeId -> total edge count in current rendered set

// ── Degree calculation ────────────────────────────────────────────────────────

function computeDegree(nodes, edges) {
  const deg = {};
  for (const n of nodes) deg[n.id] = 0;
  for (const e of edges) {
    if (deg[e.source] !== undefined) deg[e.source]++;
    if (deg[e.target] !== undefined) deg[e.target]++;
  }
  return deg;
}

// ── Node / edge vis options ───────────────────────────────────────────────────

function nodeOptions(node, degree) {
  const deg = degree[node.id] || 0;
  const isVisible = deg >= LABEL_VISIBLE_DEGREE;

  // Concept boxes
  if (node.kind === "concept") {
    const fontSize = isVisible ? Math.min(14, 10 + Math.log2(deg + 1)) : 0;
    const displayLabel = isVisible ? node.label : "";
    return {
      id: node.id,
      label: displayLabel,
      title: node.label,   // always in hover tooltip
      group: node.kind,
      color: {
        background: COLORS.concept,
        border: deg >= TOP_THEMES_DEGREE ? "#c87d00" : "#1a1a1a",
        highlight: { background: "#ffd166", border: "#c87d00" },
      },
      font: { color: "#0e1116", size: fontSize },
      shape: "box",
      margin: 4,
      meta: node.meta || {},
      kind: node.kind,
      _fullLabel: node.label,
    };
  }

  // Person / artifact dots — size by degree
  const baseSize = node.kind === "artifact" ? 10 : 12;
  const size = Math.min(baseSize + deg * 1.2, node.kind === "artifact" ? 22 : 28);
  const displayLabel = node.kind === "artifact"
    ? truncate(node.label, ARTIFACT_LABEL_MAX)
    : node.label;
  const fontColor = "#e6edf3";

  return {
    id: node.id,
    label: displayLabel,
    title: node.label,
    group: node.kind,
    color: {
      background: COLORS[node.kind] || "#aaa",
      border: "#1a1a1a",
      highlight: { background: "#fff", border: "#1a1a1a" },
    },
    font: { color: fontColor, size: 12 },
    shape: "dot",
    size,
    meta: node.meta || {},
    kind: node.kind,
    _fullLabel: node.label,
  };
}

function edgeOptions(edge) {
  const isShared = edge.kind === "shared_language";
  const isTrust = edge.kind === "trust";
  return {
    from: edge.source,
    to: edge.target,
    width: Math.min(0.5 + (edge.weight || 1) * 0.4, 5),
    color: {
      color: isTrust ? "#3a8a6a" : isShared ? "#3a4250" : "#4a5060",
      opacity: isTrust ? 0.8 : 0.55,
    },
    smooth: { type: "continuous" },
    meta: edge.meta || {},
    kind: edge.kind,
  };
}

// ── Render ────────────────────────────────────────────────────────────────────

function renderGraph(graph) {
  const container = document.getElementById("graph");

  if (network) {
    network.destroy();
    network = null;
  }

  currentDegree = computeDegree(graph.nodes, graph.edges);

  const visNodes = new vis.DataSet(graph.nodes.map((n) => nodeOptions(n, currentDegree)));
  const visEdges = new vis.DataSet(graph.edges.map(edgeOptions));
  const data = { nodes: visNodes, edges: visEdges };

  const options = {
    physics: {
      stabilization: { enabled: true, iterations: 120, updateInterval: 30 },
      barnesHut: {
        gravitationalConstant: -12000,
        centralGravity: 0.15,
        springLength: 180,
        springConstant: 0.04,
        damping: 0.12,
      },
    },
    interaction: { hover: true, tooltipDelay: 150 },
    layout: { improvedLayout: false },
  };

  network = new vis.Network(container, data, options);
  network.fit();

  network.on("stabilizationIterationsDone", () => network.fit());

  network.on("click", (params) => {
    if (params.nodes.length) {
      const node = visNodes.get(params.nodes[0]);
      showNodeDetail(node);
    } else if (params.edges.length) {
      const edge = visEdges.get(params.edges[0]);
      showEdgeDetail(edge, visNodes);
    }
  });
}

// ── Detail panel ──────────────────────────────────────────────────────────────

function showNodeDetail(node) {
  const detail = document.getElementById("detail");
  const meta = node.meta || {};
  const label = node._fullLabel || node.label;
  let html = `<h2>${escapeHtml(label)}</h2>`;
  html += `<div class="kind">${escapeHtml(node.kind)}${meta.kind ? " &middot; " + escapeHtml(meta.kind) : ""}</div>`;
  if (meta.one_line) {
    html += `<p>${escapeHtml(meta.one_line)}</p>`;
  }
  if (meta.aliases && meta.aliases.length) {
    html += `<p class="source">Also known as: ${meta.aliases.map(escapeHtml).join(", ")}</p>`;
  }
  if (meta.source_url) {
    html += `<p class="source"><a href="${meta.source_url}" target="_blank" rel="noopener">Open source</a></p>`;
  }
  // Show degree
  const deg = currentDegree[node.id] || 0;
  html += `<p class="source">${deg} connection${deg !== 1 ? "s" : ""} in current view</p>`;
  detail.innerHTML = html;
}

function showEdgeDetail(edge, visNodes) {
  const detail = document.getElementById("detail");
  const fromNode = visNodes.get(edge.from);
  const toNode = visNodes.get(edge.to);
  const fromLabel = (fromNode && (fromNode._fullLabel || fromNode.label)) || edge.from;
  const toLabel = (toNode && (toNode._fullLabel || toNode.label)) || edge.to;
  let html = `<h2>${escapeHtml(fromLabel)} &rarr; ${escapeHtml(toLabel)}</h2>`;
  html += `<div class="kind">${escapeHtml(EDGE_LABELS[edge.kind] || edge.kind)}</div>`;
  if (edge.meta && edge.meta.quote) {
    html += `<blockquote>${escapeHtml(edge.meta.quote)}</blockquote>`;
  }
  detail.innerHTML = html;
}

// ── Filters ───────────────────────────────────────────────────────────────────

function applyFilter(edgeKind) {
  if (!fullGraph) return;

  let nodes, edges;

  if (edgeKind === "top") {
    // Compute shared_language degree across the full graph
    const slDeg = {};
    for (const e of fullGraph.edges) {
      if (e.kind === "shared_language") {
        slDeg[e.source] = (slDeg[e.source] || 0) + 1;
        slDeg[e.target] = (slDeg[e.target] || 0) + 1;
      }
    }
    // Keep concept nodes above threshold, plus all people and artifacts
    const keepIds = new Set(
      fullGraph.nodes
        .filter((n) => n.kind !== "concept" || (slDeg[n.id] || 0) >= TOP_THEMES_DEGREE)
        .map((n) => n.id)
    );
    nodes = fullGraph.nodes.filter((n) => keepIds.has(n.id));
    edges = fullGraph.edges.filter(
      (e) =>
        keepIds.has(e.source) &&
        keepIds.has(e.target) &&
        (e.kind === "shared_language" || e.kind === "authored_by" || e.kind === "appears_in")
    );
  } else if (edgeKind === "all") {
    nodes = fullGraph.nodes;
    edges = fullGraph.edges;
  } else {
    // shared_language or trust
    edges = fullGraph.edges.filter(
      (e) => e.kind === edgeKind || e.kind === "authored_by" || e.kind === "appears_in"
    );
    const ids = new Set();
    for (const e of edges) {
      ids.add(e.source);
      ids.add(e.target);
    }
    nodes = fullGraph.nodes.filter((n) => ids.has(n.id));
  }

  renderGraph({ ...fullGraph, nodes, edges });
}

// ── Search ────────────────────────────────────────────────────────────────────

function initSearch() {
  const input = document.getElementById("graph-search");
  const dropdown = document.getElementById("graph-search-dropdown");
  if (!input || !dropdown) return;

  let activeIdx = -1;
  let matches = [];

  function updateDropdown(query) {
    dropdown.innerHTML = "";
    activeIdx = -1;
    if (!query || !fullGraph) {
      dropdown.hidden = true;
      return;
    }
    const q = query.toLowerCase();
    matches = fullGraph.nodes
      .filter((n) => n.label.toLowerCase().includes(q))
      .sort((a, b) => {
        // Exact prefix match first
        const aStart = a.label.toLowerCase().startsWith(q) ? 0 : 1;
        const bStart = b.label.toLowerCase().startsWith(q) ? 0 : 1;
        return aStart - bStart || a.label.localeCompare(b.label);
      })
      .slice(0, 10);

    if (!matches.length) {
      dropdown.hidden = true;
      return;
    }

    for (let i = 0; i < matches.length; i++) {
      const n = matches[i];
      const item = document.createElement("button");
      item.type = "button";
      item.className = "search-item";
      item.dataset.nodeId = n.id;
      item.innerHTML = `<span class="search-kind search-kind-${n.kind}"></span>${escapeHtml(n.label)}`;
      item.addEventListener("mousedown", (evt) => {
        evt.preventDefault();
        selectNode(n);
      });
      dropdown.appendChild(item);
    }
    dropdown.hidden = false;
  }

  function selectNode(node) {
    input.value = node.label;
    dropdown.hidden = true;
    window.btoFocusOnNode(node.id);
  }

  function setActive(idx) {
    const items = dropdown.querySelectorAll(".search-item");
    items.forEach((el, i) => el.classList.toggle("active", i === idx));
    activeIdx = idx;
  }

  input.addEventListener("input", () => updateDropdown(input.value.trim()));

  input.addEventListener("keydown", (evt) => {
    const items = dropdown.querySelectorAll(".search-item");
    if (evt.key === "ArrowDown") {
      evt.preventDefault();
      setActive(Math.min(activeIdx + 1, items.length - 1));
    } else if (evt.key === "ArrowUp") {
      evt.preventDefault();
      setActive(Math.max(activeIdx - 1, 0));
    } else if (evt.key === "Enter") {
      evt.preventDefault();
      if (activeIdx >= 0 && matches[activeIdx]) {
        selectNode(matches[activeIdx]);
      } else if (matches[0]) {
        selectNode(matches[0]);
      }
    } else if (evt.key === "Escape") {
      dropdown.hidden = true;
    }
  });

  input.addEventListener("blur", () => {
    // Short delay so mousedown on an item fires first
    setTimeout(() => { dropdown.hidden = true; }, 150);
  });

  input.addEventListener("focus", () => {
    if (input.value.trim()) updateDropdown(input.value.trim());
  });
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function escapeHtml(value) {
  if (value == null) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ── Init ──────────────────────────────────────────────────────────────────────

async function init() {
  let res;
  try {
    res = await fetch("/api/graph");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
  } catch (err) {
    document.getElementById("graph").innerHTML = `<p style="color:#f87171;padding:20px">Failed to load graph: ${err.message}</p>`;
    return;
  }
  fullGraph = await res.json();
  window.fullGraph = fullGraph;

  document.getElementById("meta").textContent =
    `${fullGraph.nodes.length} nodes, ${fullGraph.edges.length} edges. Source: ${fullGraph.source}.`;

  // Default: top themes view
  applyFilter("top");

  document.querySelectorAll("nav#filters button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("nav#filters button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      applyFilter(btn.dataset.edge);
    });
  });

  initSearch();
}

// ── Public hooks ──────────────────────────────────────────────────────────────

window.btoFitGraph = function () {
  if (network) network.fit();
};

window.btoFocusOnNode = function (nodeId) {
  if (!fullGraph) return;
  const target = fullGraph.nodes.find((n) => n.id === nodeId);
  if (!target) return;

  const allBtn = document.querySelector('nav#filters button[data-edge="all"]');
  if (allBtn && !allBtn.classList.contains("active")) {
    allBtn.click();
  }

  setTimeout(() => {
    if (!network) return;
    try {
      network.selectNodes([nodeId]);
      network.focus(nodeId, {
        scale: 1.4,
        animation: { duration: 500, easingFunction: "easeInOutQuad" },
      });
    } catch (_) {
      if (network.fit) network.fit();
    }
    showNodeDetail({ ...target, meta: target.meta || {}, _fullLabel: target.label });
  }, 80);
};

init();
