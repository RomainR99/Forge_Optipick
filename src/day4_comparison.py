"""
Jour 4 : Comparaison des stratégies d'allocation.
Métriques : distance (proxy), temps (estimé), coût.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Any

from src.models import Order, Agent, Product, Warehouse
from src.loader import parse_orders, parse_agents
from src.constraints import get_product_zone


def _estimate_order_distance(warehouse: Warehouse, order: Order) -> int:
    entry = warehouse.entry_point
    return sum(entry.manhattan(loc) for loc in order.unique_locations)


def compute_metrics(
    warehouse: Warehouse,
    orders: List[Order],
    agents: List[Agent],
    assignment: Dict[str, Optional[str]],
    products_by_id: Dict[str, Product],
) -> Dict[str, Any]:
    """
    Calcule distance totale (proxy), temps total estimé, coût total estimé.
    """
    orders_by_id = {order.id: order for order in orders}
    agents_by_id = {agent.id: agent for agent in agents}

    total_distance = 0
    total_time_sec = 0.0
    total_cost = 0.0

    agent_orders: Dict[str, List[Order]] = {agent.id: [] for agent in agents}
    for order_id, agent_id in assignment.items():
        if agent_id is None:
            continue
        order = orders_by_id.get(order_id)
        if order:
            agent_orders[agent_id].append(order)

    for agent_id, assigned_orders in agent_orders.items():
        if not assigned_orders:
            continue
        agent = agents_by_id.get(agent_id)
        if not agent:
            continue
        dist = sum(_estimate_order_distance(warehouse, order) for order in assigned_orders)
        n_items = sum(len(order.items) for order in assigned_orders)
        picking_sec = n_items * 30
        travel_sec = dist / agent.speed if agent.speed > 0 else 0
        time_sec = travel_sec + picking_sec
        cost = time_sec * (agent.cost_per_hour / 3600.0)
        total_distance += dist
        total_time_sec += time_sec
        total_cost += cost

    n_assigned = sum(1 for assigned_agent_id in assignment.values() if assigned_agent_id is not None)
    n_unassigned = len(assignment) - n_assigned

    return {
        "n_orders": len(orders),
        "n_assigned": n_assigned,
        "n_unassigned": n_unassigned,
        "distance_proxy": total_distance,
        "time_sec": total_time_sec,
        "time_min": total_time_sec / 60.0,
        "cost_euros": round(total_cost, 2),
    }


def _sort_orders_by_received_time(orders: List[Order]) -> List[Order]:
    def to_minutes(hhmm: str) -> int:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)
    return sorted(orders, key=lambda order: to_minutes(order.received_time))


def run_comparison(
    warehouse: Warehouse,
    orders: List[Order],
    agents: List[Agent],
    products_by_id: Dict[str, Product],
    use_minizinc: bool = True,
    use_cpsat: bool = True,
    use_batching: bool = True,
    solver_name: str = "cbc",
) -> Dict[str, Dict[str, Any]]:
    """
    Lance les stratégies demandées et retourne les métriques par stratégie.
    """
    results = {}
    orders_sorted = _sort_orders_by_received_time(orders)

    # 1. Glouton First-Fit (Jour 1)
    from main import allocate_first_fit, apply_assignment
    agents_ff = parse_agents([{"id": agent.id, "type": agent.type, "capacity_weight": agent.capacity_weight,
                              "capacity_volume": agent.capacity_volume, "speed": agent.speed,
                              "cost_per_hour": agent.cost_per_hour, "restrictions": getattr(agent, "restrictions", {})}
                             for agent in agents])
    assign_ff = allocate_first_fit(orders_sorted, agents_ff)
    results["first_fit"] = compute_metrics(warehouse, orders_sorted, agents_ff, assign_ff, products_by_id)
    results["first_fit"]["assignment"] = assign_ff

    # 2. MiniZinc (Jour 2) si demandé
    if use_minizinc:
        try:
            from src.minizinc_solver import allocate_with_minizinc
            agents_mz = parse_agents([{"id": agent.id, "type": agent.type, "capacity_weight": agent.capacity_weight,
                                      "capacity_volume": agent.capacity_volume, "speed": agent.speed,
                                      "cost_per_hour": agent.cost_per_hour, "restrictions": getattr(agent, "restrictions", {})}
                                     for agent in agents])
            assign_mz = allocate_with_minizinc(orders_sorted, agents_mz, products_by_id, warehouse, solver_name)
            apply_assignment(assign_mz, orders_sorted, agents_mz)
            results["minizinc"] = compute_metrics(warehouse, orders_sorted, agents_mz, assign_mz, products_by_id)
            results["minizinc"]["assignment"] = assign_mz
        except Exception as e:
            results["minizinc"] = {"error": str(e)}

    # 3. CP-SAT (Jour 4)
    if use_cpsat:
        try:
            from src.allocation_cpsat import allocate_with_cpsat
            agents_cp = parse_agents([{"id": agent.id, "type": agent.type, "capacity_weight": agent.capacity_weight,
                                      "capacity_volume": agent.capacity_volume, "speed": agent.speed,
                                      "cost_per_hour": agent.cost_per_hour, "restrictions": getattr(agent, "restrictions", {})}
                                     for agent in agents])
            assign_cp = allocate_with_cpsat(orders_sorted, agents_cp, products_by_id, warehouse, objective="assign")
            apply_assignment(assign_cp, orders_sorted, agents_cp)
            results["cpsat"] = compute_metrics(warehouse, orders_sorted, agents_cp, assign_cp, products_by_id)
            results["cpsat"]["assignment"] = assign_cp
        except Exception as e:
            results["cpsat"] = {"error": str(e)}

    # 4. Batching + CP-SAT
    if use_batching and use_cpsat:
        try:
            from src.batching import build_batches, batches_to_assignment
            from src.allocation_cpsat import allocate_batches_with_cpsat
            max_w = max(agent.capacity_weight for agent in agents) if agents else 100
            max_v = max(agent.capacity_volume for agent in agents) if agents else 100
            batches = build_batches(orders_sorted, products_by_id, max_batch_weight=max_w, max_batch_volume=max_v)
            if batches:
                assign_batch = allocate_batches_with_cpsat(batches, agents, products_by_id, warehouse)
                order_assign = {}
                for order in orders_sorted:
                    order_assign[order.id] = None
                for batch_idx, batch in enumerate(batches):
                    agent_id_batch = assign_batch.get(batch_idx)
                    if agent_id_batch:
                        for order in batch.orders:
                            order_assign[order.id] = agent_id_batch
                agents_b = parse_agents([{"id": agent.id, "type": agent.type, "capacity_weight": agent.capacity_weight,
                                         "capacity_volume": agent.capacity_volume, "speed": agent.speed,
                                         "cost_per_hour": agent.cost_per_hour, "restrictions": getattr(agent, "restrictions", {})}
                                        for agent in agents])
                apply_assignment(order_assign, orders_sorted, agents_b)
                results["batching_cpsat"] = compute_metrics(warehouse, orders_sorted, agents_b, order_assign, products_by_id)
                results["batching_cpsat"]["assignment"] = order_assign
                results["batching_cpsat"]["n_batches"] = len(batches)
            else:
                results["batching_cpsat"] = {"error": "Aucun lot créé"}
        except Exception as e:
            results["batching_cpsat"] = {"error": str(e)}

    return results
