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
  artifact: "#5b5bd6",
  person: "#16795a",
  concept: "#c2750a",
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
        border: deg >= TOP_THEMES_DEGREE ? "#7c4a00" : "#d4a055",
        highlight: { background: "#fde68a", border: "#7c4a00" },
      },
      font: { color: "#3d1f00", size: fontSize },
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
  const isArtifact = node.kind === "artifact";
  const isPerson = node.kind === "person";
  const highlightBg = isArtifact ? "#a5b4fc" : isPerson ? "#6ee7b7" : "#fde68a";
  const borderColor = isArtifact ? "#3730a3" : isPerson ? "#0f5940" : "#7c4a00";

  return {
    id: node.id,
    label: displayLabel,
    title: node.label,
    group: node.kind,
    color: {
      background: COLORS[node.kind] || "#aaa",
      border: borderColor,
      highlight: { background: highlightBg, border: borderColor },
    },
    font: { color: "#ffffff", size: 12 },
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
      color: isTrust ? "#16795a" : isShared ? "#b0a090" : "#c0b8ac",
      opacity: isTrust ? 0.7 : 0.45,
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
  const nodeId = node.id;

  let html = `<h2>${escapeHtml(label)}</h2>`;
  html += `<div class="kind">${escapeHtml(node.kind)}${meta.kind ? " &middot; " + escapeHtml(meta.kind) : ""}</div>`;

  if (meta.one_line) html += `<p>${escapeHtml(meta.one_line)}</p>`;

  if (meta.aliases && meta.aliases.length) {
    html += `<p class="source">Also: ${meta.aliases.map(escapeHtml).join(", ")}</p>`;
  }

  // ── Concept: show episodes/posts where this concept appears ────────────────
  if (node.kind === "concept" && fullGraph) {
    const appearances = fullGraph.edges
      .filter((e) => e.kind === "appears_in" && e.source === nodeId)
      .map((e) => {
        const artifact = fullGraph.nodes.find((n) => n.id === e.target);
        return artifact ? { artifact, quote: (e.meta && e.meta.quote) || "" } : null;
      })
      .filter(Boolean);

    if (appearances.length) {
      const count = appearances.length;
      html += `<div class="appears-in-section">`;
      html += `<div class="appears-in-header">Came up in ${count} ${count === 1 ? "episode or post" : "episodes and posts"}</div>`;
      for (const { artifact, quote } of appearances) {
        const artifactMeta = artifact.meta || {};
        const url = artifactMeta.source_url;
        html += `<div class="appears-in-item">`;
        html += `<div class="appears-in-title">`;
        html += url
          ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(artifact.label)}</a>`
          : escapeHtml(artifact.label);
        html += `</div>`;
        if (quote) html += `<blockquote>&ldquo;${escapeHtml(quote)}&rdquo;</blockquote>`;
        html += `</div>`;
      }
      html += `</div>`;
    }
  }

  // ── Artifact: show speaker + concepts discussed ────────────────────────────
  if (node.kind === "artifact" && fullGraph) {
    if (meta.source_url) {
      html += `<p class="source"><a href="${escapeHtml(meta.source_url)}" target="_blank" rel="noopener">Open source &rarr;</a></p>`;
    }
    // Guest speaker
    const speakerEdge = fullGraph.edges.find(
      (e) => e.kind === "authored_by" && e.source === nodeId
    );
    if (speakerEdge) {
      const person = fullGraph.nodes.find((n) => n.id === speakerEdge.target);
      if (person) html += `<p class="source detail-guest">with <strong>${escapeHtml(person.label)}</strong></p>`;
    }
    // Concepts extracted from this artifact
    const concepts = fullGraph.edges
      .filter((e) => e.kind === "appears_in" && e.target === nodeId)
      .map((e) => fullGraph.nodes.find((n) => n.id === e.source))
      .filter(Boolean);

    if (concepts.length) {
      html += `<div class="appears-in-section">`;
      html += `<div class="appears-in-header">${concepts.length} ${concepts.length === 1 ? "idea" : "ideas"} surfaced in this one</div>`;
      html += `<div class="concept-list">`;
      for (const c of concepts) {
        html += `<button class="concept-tag" data-node-id="${escapeHtml(c.id)}">${escapeHtml(c.label)}</button>`;
      }
      html += `</div></div>`;
    }
  }

  // ── Person: trust graph — who they vouch for, who vouches for them ─────────
  if (node.kind === "person" && fullGraph) {
    const vouchesFor = fullGraph.edges
      .filter((e) => e.kind === "trust" && e.source === nodeId)
      .map((e) => {
        const person = fullGraph.nodes.find((n) => n.id === e.target);
        return person ? { person, quote: (e.meta && e.meta.quote) || "" } : null;
      })
      .filter(Boolean);

    const vouchedBy = fullGraph.edges
      .filter((e) => e.kind === "trust" && e.target === nodeId)
      .map((e) => {
        const person = fullGraph.nodes.find((n) => n.id === e.source);
        return person ? { person, quote: (e.meta && e.meta.quote) || "" } : null;
      })
      .filter(Boolean);

    if (vouchesFor.length || vouchedBy.length) {
      html += `<div class="trust-section">`;
      if (vouchedBy.length) {
        html += `<div class="trust-header">People who trust them</div>`;
        for (const { person, quote } of vouchedBy) {
          html += `<div class="trust-item"><div class="trust-person">${escapeHtml(person.label)}</div>`;
          if (quote) html += `<blockquote>&ldquo;${escapeHtml(quote)}&rdquo;</blockquote>`;
          html += `</div>`;
        }
      }
      if (vouchesFor.length) {
        html += `<div class="trust-header">People they trust</div>`;
        for (const { person, quote } of vouchesFor) {
          html += `<div class="trust-item"><div class="trust-person">${escapeHtml(person.label)}</div>`;
          if (quote) html += `<blockquote>&ldquo;${escapeHtml(quote)}&rdquo;</blockquote>`;
          html += `</div>`;
        }
      }
      html += `</div>`;
    }
  }

  detail.innerHTML = html;

  // Wire concept-tag clicks to focus that node
  detail.querySelectorAll(".concept-tag[data-node-id]").forEach((btn) => {
    btn.addEventListener("click", () => window.btoFocusOnNode(btn.dataset.nodeId));
  });
}

function showEdgeDetail(edge, visNodes) {
  const detail = document.getElementById("detail");
  const fromNode = visNodes.get(edge.from);
  const toNode = visNodes.get(edge.to);
  const fromLabel = (fromNode && (fromNode._fullLabel || fromNode.label)) || edge.from;
  const toLabel = (toNode && (toNode._fullLabel || toNode.label)) || edge.to;
  const fromKind = fromNode && fromNode.kind;
  const toKind = toNode && toNode.kind;

  const connectionNote = {
    shared_language: "These two share a common language — they reach for the same words.",
    trust: "There's a trust relationship here. One vouched for the other.",
    authored_by: "This episode or post features this person.",
    appears_in: "This idea surfaces in that episode or post.",
  }[edge.kind] || "";

  let html = `<p class="edge-connection-note">${escapeHtml(connectionNote)}</p>`;
  html += `<h2 class="edge-title">${escapeHtml(fromLabel)}</h2>`;
  html += `<div class="edge-arrow-row"><span class="edge-arrow">↓</span><span class="kind">${escapeHtml(EDGE_LABELS[edge.kind] || edge.kind)}</span></div>`;
  html += `<h2 class="edge-title">${escapeHtml(toLabel)}</h2>`;
  if (edge.meta && edge.meta.quote) {
    html += `<blockquote class="edge-quote">&ldquo;${escapeHtml(edge.meta.quote)}&rdquo;</blockquote>`;
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
