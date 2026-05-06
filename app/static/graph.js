// Beneath the Org Chart - frontend
//
// Loads /api/graph, renders a force-directed network using vis-network, and
// wires the edge-kind filter buttons and a side-panel detail view.

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

let fullGraph = null;
let network = null;

function nodeOptions(node) {
  return {
    id: node.id,
    label: node.label,
    group: node.kind,
    color: { background: COLORS[node.kind] || "#aaa", border: "#1a1a1a" },
    font: { color: "#0e1116", size: 13 },
    shape: node.kind === "concept" ? "box" : "dot",
    meta: node.meta || {},
    kind: node.kind,
  };
}

function edgeOptions(edge) {
  const isShared = edge.kind === "shared_language";
  return {
    from: edge.source,
    to: edge.target,
    width: Math.min(1 + (edge.weight || 1), 6),
    color: { color: isShared ? "#3a4250" : "#5a6172", opacity: 0.7 },
    smooth: { type: "continuous" },
    meta: edge.meta || {},
    kind: edge.kind,
  };
}

function renderGraph(graph) {
  const container = document.getElementById("graph");

  if (network) {
    network.destroy();
    network = null;
  }

  const data = {
    nodes: new vis.DataSet(graph.nodes.map(nodeOptions)),
    edges: new vis.DataSet(graph.edges.map(edgeOptions)),
  };
  const options = {
    physics: {
      stabilization: { enabled: false },
      barnesHut: { gravitationalConstant: -8000, springLength: 140 },
    },
    interaction: { hover: true, tooltipDelay: 200 },
  };
  network = new vis.Network(container, data, options);
  network.fit();
  network.on("click", (params) => {
    if (params.nodes.length) {
      const node = data.nodes.get(params.nodes[0]);
      showNodeDetail(node);
    } else if (params.edges.length) {
      const edge = data.edges.get(params.edges[0]);
      showEdgeDetail(edge, data);
    }
  });
}

function showNodeDetail(node) {
  const detail = document.getElementById("detail");
  const meta = node.meta || {};
  let html = `<h2>${escapeHtml(node.label)}</h2>`;
  html += `<div class="kind">${escapeHtml(node.kind)}${meta.kind ? " &middot; " + escapeHtml(meta.kind) : ""}</div>`;
  if (meta.one_line) {
    html += `<p>${escapeHtml(meta.one_line)}</p>`;
  }
  if (meta.aliases && meta.aliases.length) {
    html += `<p class="source">Also: ${meta.aliases.map(escapeHtml).join(", ")}</p>`;
  }
  if (meta.source_url) {
    html += `<p class="source"><a href="${meta.source_url}" target="_blank" rel="noopener">Open source</a></p>`;
  }
  detail.innerHTML = html;
}

function showEdgeDetail(edge, data) {
  const detail = document.getElementById("detail");
  const fromNode = data.nodes.get(edge.from);
  const toNode = data.nodes.get(edge.to);
  let html = `<h2>${escapeHtml(fromNode.label)} &rarr; ${escapeHtml(toNode.label)}</h2>`;
  html += `<div class="kind">${escapeHtml(EDGE_LABELS[edge.kind] || edge.kind)}</div>`;
  if (edge.meta && edge.meta.quote) {
    html += `<blockquote>${escapeHtml(edge.meta.quote)}</blockquote>`;
  }
  detail.innerHTML = html;
}

function applyFilter(edgeKind) {
  if (!fullGraph) return;
  let nodes;
  let edges;
  if (edgeKind === "all") {
    nodes = fullGraph.nodes;
    edges = fullGraph.edges;
  } else {
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

function escapeHtml(value) {
  if (value == null) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

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
  // Expose for lookup.js to resolve concept ids to labels without a refetch.
  window.fullGraph = fullGraph;
  document.getElementById("meta").textContent = `${fullGraph.nodes.length} nodes, ${fullGraph.edges.length} edges. Source: ${fullGraph.source}.`;

  applyFilter("shared_language");

  document.querySelectorAll("nav#filters button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("nav#filters button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      applyFilter(btn.dataset.edge);
    });
  });
}

// Expose a re-fit hook so main.js can ask the graph to recompute its frame
// when the Atlas surface becomes visible again after being hidden.
window.btoFitGraph = function () {
  if (network) network.fit();
};

init();
