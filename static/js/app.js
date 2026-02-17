/**
 * OptiPick — Interface web Jour 6
 * Affichage entrepôt, animation agents, formulaire commandes, stats en direct
 */

function getAllocParams() {
  const sel = document.getElementById("alloc-method");
  return { alloc: sel ? sel.value : "first_fit", solver: "cbc" };
}

const API = {
  warehouse: () => fetch("/api/warehouse").then((r) => r.json()),
  products: () => fetch("/api/products").then((r) => r.json()),
  agents: () => fetch("/api/agents").then((r) => r.json()),
  stats: (params) => {
    const q = new URLSearchParams(params || getAllocParams()).toString();
    return fetch("/api/stats" + (q ? "?" + q : "")).then((r) => r.json());
  },
  orders: (params) => {
    const q = new URLSearchParams(params || getAllocParams()).toString();
    return fetch("/api/orders" + (q ? "?" + q : "")).then((r) => r.json());
  },
  addOrder: (body) =>
    fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...getAllocParams(), ...body }),
    }).then((r) => r.json()),
};

// État
let warehouse = null;
let products = [];
let agents = [];
let agentPositions = {};
let agentRoutes = {};
let agentProgress = {};
let assignment = {};
let stats = {};
let ordersMetrics = [];
let canvasEl = null;
let ctx = null;
let scale = 1;
let offsetX = 0;
let offsetY = 0;
const ANIMATION_SPEED = 0.0006;
const FLOOR_LABEL_MARGIN = 52;
let animationId = null;

const ZONE_COLORS = {
  A: "#3498db",
  B: "#2ecc71",
  C: "#e74c3c",
  D: "#9b59b6",
  E: "#f39c12",
};
const AGENT_COLORS = { robot: "#7dcfff", human: "#bb9af7", cart: "#9ece6a" };
const HUMAN_FLOOR_COLOR = "#ff9e64";

function toCanvas(x, y) {
  return {
    x: offsetX + x * scale,
    y: offsetY + y * scale,
  };
}

function drawWarehouseBase() {
  if (!ctx || !warehouse) return;
  const w = warehouse.dimensions?.width || 10;
  const h = warehouse.dimensions?.height || 8;
  const zones = warehouse.zones || {};
  const entry = warehouse.entry_point || [0, 0];
  const entryX = Array.isArray(entry) ? entry[0] : entry.x;
  const entryY = Array.isArray(entry) ? entry[1] : entry.y;

  ctx.fillStyle = "rgba(0,0,0,0.25)";
  ctx.fillRect(0, 0, canvasEl.width, canvasEl.height);

  // Étages (labels à gauche)
  ctx.fillStyle = "rgba(255,255,255,0.85)";
  ctx.font = `${Math.max(10, Math.min(14, scale * 0.5))}px monospace`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  for (let j = 0; j <= h; j++) {
    const label = j === 0 ? "RDC" : `Étage ${j}`;
    const cy = offsetY + (j + 0.5) * scale;
    ctx.fillText(label, FLOOR_LABEL_MARGIN / 2, cy);
  }

  // Grille
  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.lineWidth = 1;
  for (let i = 0; i <= w; i++) {
    const p = toCanvas(i, 0);
    ctx.beginPath();
    ctx.moveTo(p.x, 0);
    ctx.lineTo(p.x, canvasEl.height);
    ctx.stroke();
  }
  for (let j = 0; j <= h; j++) {
    const p = toCanvas(0, j);
    ctx.beginPath();
    ctx.moveTo(FLOOR_LABEL_MARGIN, p.y);
    ctx.lineTo(canvasEl.width, p.y);
    ctx.stroke();
  }

  // Zones
  for (const [zoneName, zone] of Object.entries(zones)) {
    const coords = zone.coords || [];
    const color = ZONE_COLORS[zoneName] || "#666";
    ctx.fillStyle = color;
    ctx.globalAlpha = 0.35;
    for (const c of coords) {
      const [cx, cy] = Array.isArray(c) ? c : [c.x, c.y];
      const p = toCanvas(cx + 0.5, cy + 0.5);
      ctx.beginPath();
      ctx.arc(p.x, p.y, scale * 0.45, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    for (const c of coords) {
      const [cx, cy] = Array.isArray(c) ? c : [c.x, c.y];
      const p = toCanvas(cx + 0.5, cy + 0.5);
      ctx.strokeRect(p.x - scale * 0.4, p.y - scale * 0.4, scale * 0.8, scale * 0.8);
    }
  }

  // Emplacements produits (points discrets)
  if (products.length) {
    ctx.fillStyle = "rgba(255,255,255,0.2)";
    for (const p of products) {
      const loc = p.location || [0, 0];
      const [lx, ly] = Array.isArray(loc) ? loc : [loc.x, loc.y];
      const q = toCanvas(lx + 0.5, ly + 0.5);
      ctx.beginPath();
      ctx.arc(q.x, q.y, Math.max(2, scale * 0.15), 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // Entrée
  const ep = toCanvas(entryX + 0.5, entryY + 0.5);
  ctx.fillStyle = "#fff";
  ctx.strokeStyle = "#7aa2f7";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(ep.x, ep.y - scale * 0.4);
  ctx.lineTo(ep.x + scale * 0.35, ep.y + scale * 0.35);
  ctx.lineTo(ep.x - scale * 0.35, ep.y + scale * 0.35);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
}

/**
 * Déplacement en Manhattan : horizontal puis vertical. Pas de diagonale.
 * - Robots et chariots : restent sur le même étage (pas de déplacement vertical à l'écran).
 * - Humains : se déplacent aussi verticalement (changement d'étage) avec indication orange.
 */
function getAgentPosition(agentId, agentType) {
  const route = agentRoutes[agentId];
  if (!route || route.length === 0) return null;
  if (route.length === 1) return { x: route[0].x + 0.5, y: route[0].y + 0.5, isVerticalSegment: false };
  let p = agentProgress[agentId] ?? 0;
  p = p % 1;
  const n = route.length;
  const seg = (n - 1) * p;
  const i = Math.min(Math.floor(seg), n - 2);
  const t = seg - i;
  const a = route[i];
  const b = route[i + 1];
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const onlyHorizontal = agentType === "robot" || agentType === "cart";
  let x, y, isVerticalSegment = false;
  if (t <= 0.5) {
    const th = t * 2;
    x = a.x + dx * th;
    y = a.y;
  } else {
    const tv = (t - 0.5) * 2;
    x = b.x;
    if (onlyHorizontal) {
      y = a.y;
    } else {
      y = a.y + dy * tv;
      if (dy !== 0) isVerticalSegment = true;
    }
  }
  return {
    x: x + 0.5,
    y: y + 0.5,
    isVerticalSegment,
  };
}

function drawAgents() {
  if (!ctx || !warehouse) return;
  const agentList = agents || [];
  const entry = warehouse.entry_point || [0, 0];
  const entryX = Array.isArray(entry) ? entry[0] : entry.x;
  const entryY = Array.isArray(entry) ? entry[1] : entry.y;
  for (const agent of agentList) {
    const type = agent.type || "robot";
    const pos = getAgentPosition(agent.id, type);
    let color = AGENT_COLORS[type] || "#7dcfff";
    if (type === "human" && pos && pos.isVerticalSegment) {
      color = HUMAN_FLOOR_COLOR;
    }
    const px = pos ? pos.x : entryX + 0.5;
    const py = pos ? pos.y : entryY + 0.5;
    const p = toCanvas(px, py);
    ctx.fillStyle = color;
    ctx.strokeStyle = "rgba(0,0,0,0.5)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, scale * 0.35, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#1a1b26";
    ctx.font = `bold ${Math.max(8, scale * 0.25)}px monospace`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(agent.id, p.x, p.y);
  }
}

function drawWarehouse() {
  drawWarehouseBase();
  drawAgents();
}

function resizeCanvas() {
  if (!canvasEl || !warehouse) return;
  const w = warehouse.dimensions?.width || 10;
  const h = warehouse.dimensions?.height || 8;
  const wrap = canvasEl.parentElement;
  const maxW = wrap.clientWidth;
  const maxH = Math.max(320, wrap.clientHeight || 320);
  const cellSize = Math.min((maxW - FLOOR_LABEL_MARGIN) / (w + 1), maxH / (h + 1));
  scale = cellSize;
  offsetX = FLOOR_LABEL_MARGIN + scale * 0.5;
  offsetY = scale * 0.5;
  canvasEl.width = FLOOR_LABEL_MARGIN + (w + 1) * scale;
  canvasEl.height = (h + 1) * scale;
  canvasEl.style.width = canvasEl.width + "px";
  canvasEl.style.height = canvasEl.height + "px";
  drawWarehouse();
}

function refreshStats() {
  API.stats()
    .then((data) => {
      if (data.error) {
        console.warn("Stats error:", data.error);
        return;
      }
      stats = data.stats || {};
      ordersMetrics = data.orders_metrics || [];
      agentPositions = data.agent_positions || {};
      agentRoutes = data.agent_routes || {};
      assignment = data.assignment || {};
      for (const aid of Object.keys(agentRoutes)) {
        if (agentProgress[aid] === undefined) agentProgress[aid] = 0;
      }
      const byType = stats.by_type || {};
      document.getElementById("stat-orders").textContent = stats.n_orders ?? 0;
      document.getElementById("stat-assigned").textContent = stats.n_assigned ?? 0;
      document.getElementById("stat-unassigned").textContent = stats.n_unassigned ?? 0;
      document.getElementById("stat-distance").textContent = stats.total_distance ?? 0;
      document.getElementById("stat-time").textContent = stats.total_time_min ?? 0;
      document.getElementById("stat-cost").textContent = stats.total_cost_euros ?? 0;
      let html = "";
      for (const [type, t] of Object.entries(byType)) {
        const label = type === "robot" ? "Robots" : type === "human" ? "Humains" : "Chariots";
        html += `<div><span>${label}</span><span>${t.orders || 0} cmd / ${t.count || 0} agent(s)</span></div>`;
      }
      document.getElementById("stats-by-type").innerHTML = html || "<div>Aucun agent</div>";
      const tbody = document.getElementById("orders-metrics-body");
      if (tbody) {
        tbody.innerHTML = ordersMetrics.map((m) =>
          `<tr><td>${m.order_id}</td><td>${m.agent_id || "—"}</td><td>${m.distance}</td><td>${m.time_min}</td><td>${m.cost_euros}</td></tr>`
        ).join("") || "<tr><td colspan=\"5\">Aucune donnée</td></tr>";
      }
      if (ctx && canvasEl) drawWarehouse();
    })
    .catch((e) => console.warn("Refresh stats failed", e));
}

function animationLoop() {
  if (!ctx || !canvasEl || !warehouse) {
    animationId = requestAnimationFrame(animationLoop);
    return;
  }
  for (const aid of Object.keys(agentProgress)) {
    agentProgress[aid] = (agentProgress[aid] + ANIMATION_SPEED) % 1;
  }
  drawWarehouseBase();
  drawAgents();
  animationId = requestAnimationFrame(animationLoop);
}

function loadProductsForForm() {
  API.products().then((list) => {
    products = list;
    const selects = document.querySelectorAll(".product-select");
    const optHtml = list
      .map((p) => `<option value="${p.id}">${p.id} — ${(p.name || p.id).slice(0, 30)}</option>`)
      .join("");
    selects.forEach((sel) => {
      sel.innerHTML = '<option value="">— Choisir un produit —</option>' + optHtml;
    });
  });
}

function addProductRow() {
  const container = document.getElementById("order-items");
  const row = document.createElement("div");
  row.className = "order-item-row";
  const select = document.createElement("select");
  select.name = "product_id";
  select.className = "product-select";
  select.innerHTML =
    '<option value="">— Choisir —</option>' +
    (products || [])
      .map((p) => `<option value="${p.id}">${p.id} — ${(p.name || p.id).slice(0, 25)}</option>`)
      .join("");
  const input = document.createElement("input");
  input.type = "number";
  input.name = "quantity";
  input.value = 1;
  input.min = 1;
  input.max = 99;
  row.appendChild(select);
  row.appendChild(input);
  container.appendChild(row);
}

function submitOrder(e) {
  e.preventDefault();
  const msgEl = document.getElementById("form-message");
  const items = [];
  document.querySelectorAll(".order-item-row").forEach((row) => {
    const sel = row.querySelector('select[name="product_id"]');
    const qty = row.querySelector('input[name="quantity"]');
    const pid = sel?.value;
    if (pid) items.push({ product_id: pid, quantity: parseInt(qty?.value || 1, 10) });
  });
  if (items.length === 0) {
    msgEl.textContent = "Ajoutez au moins un produit.";
    msgEl.className = "message error";
    return;
  }
  const body = {
    received_time: document.getElementById("received_time").value || "12:00",
    deadline: document.getElementById("deadline").value || "18:00",
    priority: document.getElementById("priority").value || "standard",
    items,
  };
  API.addOrder(body).then((data) => {
    if (data.ok) {
      msgEl.textContent = `Commande ${data.order_id} créée.`;
      msgEl.className = "message success";
      if (data.stats) {
        stats = data.stats;
        ordersMetrics = data.orders_metrics || ordersMetrics;
        agentPositions = data.agent_positions || {};
        agentRoutes = data.agent_routes || agentRoutes;
        for (const aid of Object.keys(agentRoutes)) {
          if (agentProgress[aid] === undefined) agentProgress[aid] = 0;
        }
        document.getElementById("stat-orders").textContent = data.stats.n_orders ?? 0;
        document.getElementById("stat-assigned").textContent = data.stats.n_assigned ?? 0;
        document.getElementById("stat-unassigned").textContent = data.stats.n_unassigned ?? 0;
        document.getElementById("stat-distance").textContent = data.stats.total_distance ?? 0;
        document.getElementById("stat-time").textContent = data.stats.total_time_min ?? 0;
        document.getElementById("stat-cost").textContent = data.stats.total_cost_euros ?? 0;
        const tbody = document.getElementById("orders-metrics-body");
        if (tbody) {
          tbody.innerHTML = ordersMetrics.map((m) =>
            `<tr><td>${m.order_id}</td><td>${m.agent_id || "—"}</td><td>${m.distance}</td><td>${m.time_min}</td><td>${m.cost_euros}</td></tr>`
          ).join("") || "<tr><td colspan=\"5\">Aucune donnée</td></tr>";
        }
        drawWarehouse();
      }
      setTimeout(() => (msgEl.textContent = ""), 3000);
    } else {
      msgEl.textContent = data.error || "Erreur";
      msgEl.className = "message error";
    }
  }).catch(() => {
    msgEl.textContent = "Erreur réseau.";
    msgEl.className = "message error";
  });
}

function init() {
  canvasEl = document.getElementById("warehouse-canvas");
  if (!canvasEl) return;
  ctx = canvasEl.getContext("2d");

  API.warehouse().then((w) => {
    warehouse = w;
    const zones = w.zones || {};
    const listEl = document.getElementById("zone-legend-list");
    if (listEl) {
      listEl.textContent = Object.entries(zones)
        .map(([letter, z]) => `${letter} ${z.name || letter}`)
        .join(", ") || "—";
    }
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);
    if (!animationId) animationLoop();
  });

  API.agents().then((a) => {
    agents = Array.isArray(a) ? a : [];
    refreshStats();
  });

  loadProductsForForm();
  setInterval(refreshStats, 4000);

  document.getElementById("alloc-method")?.addEventListener("change", () => refreshStats());
  document.getElementById("btn-add-row")?.addEventListener("click", addProductRow);
  document.getElementById("form-order")?.addEventListener("submit", submitOrder);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
