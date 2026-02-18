"""
Interface OptiPick avec Streamlit.
Même logique que app.py (Flask + JS) : données, allocation First-Fit ou MiniZinc, stats, carte, formulaire.

Lancer :
  streamlit run app_streamlit.py
  (ou depuis le répertoire optipick : streamlit run app_streamlit.py --server.port 8501)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

DATA_DIR = Path(__file__).parent / "data"


def _load_json(name: str):
    p = DATA_DIR / name
    if not p.exists():
        return {} if "orders" in name or "agents" in name else []
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _compute_assignment_and_stats(orders_list: list, alloc_method: str = "first_fit", solver_name: str = "cbc"):
    """Même logique que app.py : allocation + stats + routes + metrics par commande."""
    try:
        from main import (
            load_json,
            parse_warehouse,
            parse_products,
            parse_agents,
            parse_orders,
            enrich_orders,
            sort_orders_by_received_time,
            allocate_first_fit,
            apply_assignment,
        )
        wh_data = load_json(DATA_DIR / "warehouse.json")
        pr_data = load_json(DATA_DIR / "products.json")
        ag_data = _load_json("agents.json")
        warehouse = parse_warehouse(wh_data)
        products_by_id = parse_products(pr_data)
        agents = parse_agents(ag_data)
        orders = parse_orders(orders_list if isinstance(orders_list, list) else [])
        enrich_orders(orders, products_by_id)
        orders_sorted = sort_orders_by_received_time(orders)
        agents_fresh = parse_agents(deepcopy(ag_data))
        if alloc_method == "minizinc":
            try:
                from src.minizinc_solver import allocate_with_minizinc
                assignment = allocate_with_minizinc(
                    orders_sorted, agents_fresh, products_by_id, warehouse, solver_name=solver_name
                )
                apply_assignment(assignment, orders_sorted, agents_fresh)
            except Exception:
                assignment = allocate_first_fit(orders_sorted, agents_fresh)
        else:
            assignment = allocate_first_fit(orders_sorted, agents_fresh)

        n_orders = len(orders)
        n_assigned = sum(1 for a in assignment.values() if a is not None)
        by_type = {}
        for agent in agents_fresh:
            t = agent.type
            if t not in by_type:
                by_type[t] = {"count": 0, "orders": 0}
            by_type[t]["count"] += 1
        for oid, aid in assignment.items():
            if aid is None:
                continue
            for agent in agents_fresh:
                if agent.id == aid:
                    by_type[agent.type]["orders"] += 1
                    break

        entry = warehouse.entry_point
        agent_routes = {}
        orders_by_agent = {}
        for oid, aid in assignment.items():
            if aid is None:
                continue
            orders_by_agent.setdefault(aid, [])
            orders_by_agent[aid].append(oid)
        orders_by_id = {o.id: o for o in orders_sorted}
        for agent in agents_fresh:
            aid = agent.id
            route = [{"x": entry.x, "y": entry.y}]
            if aid in orders_by_agent:
                for order_id in orders_by_agent[aid]:
                    order = orders_by_id.get(order_id)
                    if order and getattr(order, "unique_locations", None):
                        for loc in order.unique_locations:
                            route.append({"x": loc.x, "y": loc.y})
            if agent.type in ("robot", "cart"):
                floor_y = route[0]["y"]
                route = [p for p in route if p["y"] == floor_y]
            agent_routes[aid] = route
        for agent in agents_fresh:
            if agent.id not in agent_routes:
                agent_routes[agent.id] = [{"x": entry.x, "y": entry.y}]

        def _order_distance(ord_obj):
            return sum(warehouse.entry_point.manhattan(loc) for loc in getattr(ord_obj, "unique_locations", []) or [])

        agents_by_id = {a.id: a for a in agents_fresh}
        orders_metrics = []
        total_dist = 0
        total_time_sec = 0.0
        total_cost = 0.0
        for oid, aid in assignment.items():
            order = orders_by_id.get(oid)
            agent = agents_by_id.get(aid) if aid else None
            dist = _order_distance(order) if order else 0
            time_sec = 0.0
            cost_euros = 0.0
            if order and agent:
                n_items = sum(it.quantity for it in order.items)
                travel_sec = dist / agent.speed if agent.speed > 0 else 0
                picking_sec = n_items * 30
                time_sec = travel_sec + picking_sec
                cost_euros = round(time_sec * (agent.cost_per_hour / 3600.0), 2)
                total_dist += dist
                total_time_sec += time_sec
                total_cost += cost_euros
            orders_metrics.append({
                "order_id": oid,
                "agent_id": aid or "—",
                "distance": dist,
                "time_min": round(time_sec / 60.0, 2),
                "cost_euros": cost_euros,
            })

        return {
            "assignment": assignment,
            "stats": {
                "n_orders": n_orders,
                "n_assigned": n_assigned,
                "n_unassigned": n_orders - n_assigned,
                "by_type": by_type,
                "total_distance": total_dist,
                "total_time_min": round(total_time_sec / 60.0, 2),
                "total_cost_euros": round(total_cost, 2),
            },
            "agent_routes": agent_routes,
            "orders_metrics": orders_metrics,
            "warehouse": warehouse,
            "orders_sorted": orders_sorted,
        }
    except Exception as e:
        return {
            "assignment": {},
            "stats": {"n_orders": 0, "n_assigned": 0, "n_unassigned": 0, "by_type": {}, "total_distance": 0, "total_time_min": 0, "total_cost_euros": 0},
            "agent_routes": {},
            "orders_metrics": [],
            "warehouse": None,
            "orders_sorted": [],
            "error": str(e),
        }


def _draw_warehouse_map(warehouse_data: dict, agent_routes: dict, width: int, height: int):
    """Dessine la carte de l'entrepôt avec zones et routes des agents (matplotlib)."""
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(-0.5, width)
    ax.set_ylim(-0.5, height)
    ax.set_aspect("equal")
    ax.invert_yaxis()

    zones = warehouse_data.get("zones", {})
    colors = {"A": "#4CAF50", "B": "#2196F3", "C": "#FF9800", "D": "#9C27B0", "E": "#00BCD4"}
    for zname, zinfo in zones.items():
        coords = zinfo.get("coords", [])
        c = colors.get(zname, "#ccc")
        for coord in coords:
            x, y = coord[0], coord[1]
            rect = mpatches.Rectangle((x - 0.4, y - 0.4), 0.8, 0.8, facecolor=c, edgecolor="black", linewidth=0.5)
            ax.add_patch(rect)
        if coords:
            ax.text(coords[0][0], coords[0][1] - 0.6, zname, ha="center", fontsize=9)

    entry = warehouse_data.get("entry_point", [0, 0])
    ax.plot(entry[0], entry[1], "k*", markersize=14, label="Entrée")

    route_colors = {"R1": "red", "R2": "darkred", "R3": "brown", "H1": "blue", "H2": "navy", "C1": "green", "C2": "darkgreen"}
    for aid, route in agent_routes.items():
        if not route:
            continue
        xs = [p["x"] for p in route]
        ys = [p["y"] for p in route]
        color = route_colors.get(aid, "gray")
        ax.plot(xs, ys, "o-", color=color, linewidth=2, markersize=6, label=aid)

    ax.legend(loc="upper left", fontsize=8)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Carte de l'entrepôt — zones et tournées des agents")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


# Session state : liste des commandes (initialisée depuis data/orders.json)
if "orders_list" not in st.session_state:
    raw = _load_json("orders.json")
    st.session_state.orders_list = raw if isinstance(raw, list) else []


st.set_page_config(page_title="OptiPick — Streamlit", page_icon="📦", layout="wide")

st.title("📦 OptiPick — Interface entrepôt (Streamlit)")

with st.sidebar:
    st.header("Paramètres")
    alloc_method = st.radio(
        "Méthode d'allocation",
        ["first_fit", "minizinc"],
        format_func=lambda x: "First-Fit (rapide)" if x == "first_fit" else "MiniZinc (.mzn)",
    )
    solver_name = "cbc"
    if alloc_method == "minizinc":
        solver_name = st.selectbox("Solveur MiniZinc", ["cbc", "coin-bc", "highs", "gecode"], index=1)

data = _compute_assignment_and_stats(st.session_state.orders_list, alloc_method=alloc_method, solver_name=solver_name)

if data.get("error"):
    st.error("Erreur : " + data["error"])

stats = data["stats"]
st.subheader("Statistiques")
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Commandes", stats["n_orders"])
col2.metric("Assignées", stats["n_assigned"])
col3.metric("Non assignées", stats["n_unassigned"])
col4.metric("Distance (u.)", stats["total_distance"])
col5.metric("Temps (min)", stats["total_time_min"])
col6.metric("Coût (€)", stats["total_cost_euros"])

st.write("**Par type d'agent :**")
for t, v in stats.get("by_type", {}).items():
    st.caption(f"  {t}: {v['orders']} commandes / {v['count']} agent(s)")

warehouse_data = _load_json("warehouse.json")
dims = warehouse_data.get("dimensions", {})
w = dims.get("width", 10)
h = dims.get("height", 8)
fig = _draw_warehouse_map(warehouse_data, data.get("agent_routes", {}), w, h)
st.pyplot(fig)
import matplotlib.pyplot as _plt
_plt.close(fig)

st.subheader("Performance et coût par commande")
import pandas as pd
df = pd.DataFrame(data.get("orders_metrics", []))
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Aucune commande ou aucune métrique.")

st.subheader("Ajouter une commande")
products = _load_json("products.json")
product_ids = []
product_names = {}
if isinstance(products, list):
    product_ids = [p.get("id") for p in products if p.get("id")]
    product_names = {p.get("id"): p.get("name", p.get("id")) for p in products if p.get("id")}

with st.form("add_order_form"):
    received_time = st.text_input("Heure de réception", value="12:00")
    deadline = st.text_input("Deadline", value="18:00")
    priority = st.selectbox("Priorité", ["standard", "express"])
    st.write("**Ligne de la commande**")
    pid = st.selectbox(
        "Produit",
        options=product_ids,
        format_func=lambda i: product_names.get(i, i),
    ) if product_ids else None
    qty = st.number_input("Quantité", min_value=1, value=1)
    submitted = st.form_submit_button("Créer la commande")
    if submitted and pid:
        new_id = f"Order_W{len(st.session_state.orders_list) + 1:03d}"
        new_order = {
            "id": new_id,
            "received_time": received_time,
            "deadline": deadline,
            "priority": priority,
            "items": [{"product_id": pid, "quantity": int(qty)}],
        }
        st.session_state.orders_list.append(new_order)
        st.success(f"Commande {new_id} ajoutée.")
        st.rerun()
    elif submitted and not product_ids:
        st.warning("Aucun produit chargé (vérifiez data/products.json).")
