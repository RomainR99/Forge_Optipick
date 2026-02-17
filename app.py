"""
Extension Jour 6 : Interface web OptiPick.
Flask + JavaScript — Affichage entrepôt, animation agents, formulaire commandes, stats.

Lancer :
  - Avec environnement virtuel : source venv/bin/activate  puis  python app.py
  - Ou : pip install -r requirements.txt  puis  python app.py  (ou python3 app.py)
  Puis ouvrir http://127.0.0.1:5001
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from copy import deepcopy

# Ajouter le répertoire parent pour importer main et src
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, jsonify, request

# Chargement des données au démarrage
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"

app = Flask(__name__, template_folder="templates", static_folder="static")

# Commandes en mémoire (base = fichier, POST ajoute ici sans écraser data/orders.json)
_orders_in_memory: list | None = None


def _load_json(name: str):
    p = DATA_DIR / name
    if not p.exists():
        return {} if "orders" in name or "agents" in name else []
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_warehouse():
    return _load_json("warehouse.json")


def _get_products():
    return _load_json("products.json")


def _get_agents_raw():
    return _load_json("agents.json")


def _get_orders_raw():
    global _orders_in_memory
    if _orders_in_memory is not None:
        return _orders_in_memory
    _orders_in_memory = _load_json("orders.json")
    if not isinstance(_orders_in_memory, list):
        _orders_in_memory = []
    return _orders_in_memory


def _compute_assignment_and_stats(alloc_method: str = "first_fit", solver_name: str = "cbc"):
    """Charge orders/agents, enrichit, puis allocation First-Fit ou MiniZinc (.mzn). Retourne assignment + stats + routes."""
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
        ag_data = _get_agents_raw()
        or_data = _get_orders_raw()
        warehouse = parse_warehouse(wh_data)
        products_by_id = parse_products(pr_data)
        agents = parse_agents(ag_data)
        orders = parse_orders(or_data if isinstance(or_data, list) else [])
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
            except Exception as mz_err:
                assignment = allocate_first_fit(orders_sorted, agents_fresh)
        else:
            assignment = allocate_first_fit(orders_sorted, agents_fresh)
        # Stats
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
        # Tournées des agents pour l'animation : [entrée, loc1, loc2, ...] pour chaque agent
        entry = warehouse.entry_point
        agent_positions = {}
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
            pos = {"x": entry.x, "y": entry.y}
            route = [{"x": entry.x, "y": entry.y}]
            if aid in orders_by_agent and orders_by_agent[aid]:
                for order_id in orders_by_agent[aid]:
                    order = orders_by_id.get(order_id)
                    if order and getattr(order, "unique_locations", None):
                        for loc in order.unique_locations:
                            route.append({"x": loc.x, "y": loc.y})
            if agent.type in ("robot", "cart"):
                floor_y = route[0]["y"]
                route = [p for p in route if p["y"] == floor_y]
            agent_positions[aid] = route[1] if len(route) > 1 else {"x": entry.x, "y": entry.y}
            agent_routes[aid] = route
        for agent in agents_fresh:
            if agent.id not in agent_routes:
                agent_routes[agent.id] = [{"x": entry.x, "y": entry.y}]
        # Performance et coût par commande
        def _order_distance(ord_obj):
            return sum(warehouse.entry_point.manhattan(loc) for loc in getattr(ord_obj, "unique_locations", []) or [])
        orders_by_id = {o.id: o for o in orders_sorted}
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
                "agent_id": aid,
                "distance": dist,
                "time_sec": round(time_sec, 1),
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
            "agent_positions": agent_positions,
            "agent_routes": agent_routes,
            "orders_metrics": orders_metrics,
            "orders": [
                {
                    "id": o.id,
                    "received_time": o.received_time,
                    "deadline": o.deadline,
                    "priority": o.priority,
                    "items": [{"product_id": it.product_id, "quantity": it.quantity} for it in o.items],
                }
                for o in orders_sorted
            ],
        }
    except Exception as e:
        return {
            "assignment": {},
            "stats": {"n_orders": 0, "n_assigned": 0, "n_unassigned": 0, "by_type": {}, "total_distance": 0, "total_time_min": 0, "total_cost_euros": 0},
            "agent_positions": {},
            "agent_routes": {},
            "orders_metrics": [],
            "orders": [],
            "error": str(e),
        }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/warehouse")
def api_warehouse():
    return jsonify(_get_warehouse())


@app.route("/api/products")
def api_products():
    products = _get_products()
    if isinstance(products, list):
        return jsonify([{"id": p["id"], "name": p.get("name", p["id"]), "location": p.get("location", [0, 0])} for p in products])
    return jsonify([])


@app.route("/api/agents")
def api_agents():
    return jsonify(_get_agents_raw())


def _alloc_params():
    alloc = request.args.get("alloc", "first_fit")
    solver = request.args.get("solver", "cbc")
    return alloc, solver


@app.route("/api/orders")
def api_orders():
    alloc, solver = _alloc_params()
    data = _compute_assignment_and_stats(alloc_method=alloc, solver_name=solver)
    return jsonify({"orders": data["orders"], "assignment": data["assignment"], "error": data.get("error")})


@app.route("/api/stats")
def api_stats():
    alloc, solver = _alloc_params()
    data = _compute_assignment_and_stats(alloc_method=alloc, solver_name=solver)
    return jsonify({
        "stats": data["stats"],
        "agent_positions": data["agent_positions"],
        "agent_routes": data.get("agent_routes", {}),
        "assignment": data["assignment"],
        "orders_metrics": data.get("orders_metrics", []),
        "alloc_method": alloc,
        "error": data.get("error"),
    })


@app.route("/api/assignment")
def api_assignment():
    alloc, solver = _alloc_params()
    data = _compute_assignment_and_stats(alloc_method=alloc, solver_name=solver)
    return jsonify({"assignment": data["assignment"], "agent_positions": data["agent_positions"], "error": data.get("error")})


@app.route("/api/orders", methods=["POST"])
def api_add_order():
    """Ajoute une commande (en mémoire). Body: { received_time, deadline, priority, items: [{ product_id, quantity }] }"""
    global _orders_in_memory
    body = request.get_json(force=True, silent=True) or {}
    received_time = body.get("received_time", "12:00")
    deadline = body.get("deadline", "18:00")
    priority = body.get("priority", "standard")
    items = body.get("items", [])
    if not items:
        return jsonify({"ok": False, "error": "Au moins un produit requis"}), 400
    orders = _get_orders_raw()
    if not isinstance(orders, list):
        orders = []
    new_id = f"Order_W{len(orders) + 1:03d}"
    new_order = {
        "id": new_id,
        "received_time": received_time,
        "deadline": deadline,
        "priority": priority,
        "items": [{"product_id": it.get("product_id"), "quantity": int(it.get("quantity", 1))} for it in items],
    }
    orders.append(new_order)
    _orders_in_memory = orders
    alloc = body.get("alloc", "first_fit")
    solver = body.get("solver", "cbc")
    data = _compute_assignment_and_stats(alloc_method=alloc, solver_name=solver)
    return jsonify({
        "ok": True,
        "order_id": new_id,
        "stats": data["stats"],
        "assignment": data["assignment"],
        "agent_positions": data["agent_positions"],
        "agent_routes": data.get("agent_routes", {}),
        "orders_metrics": data.get("orders_metrics", []),
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("FLASK_PORT", 5001))
    print(f"🌐 Interface web OptiPick — http://127.0.0.1:{port}")
    app.run(debug=True, host="0.0.0.0", port=port)
