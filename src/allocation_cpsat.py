"""
Jour 4 : Allocation optimale avec OR-Tools CP-SAT.
Modélisation CSP : variables assign[order_i], contraintes capacité, incompatibilités,
restrictions, objectif minimiser coût total.
"""
from __future__ import annotations

from typing import Dict, List, Optional

try:
    from ortools.sat.python import cp_model
    CPSAT_AVAILABLE = True
except ImportError:
    CPSAT_AVAILABLE = False

from src.models import Agent, Order, Product, Warehouse, Location
from src.constraints import get_product_zone, can_combine


def _zone_to_int(zone: Optional[str]) -> int:
    zone_map = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
    return zone_map.get(zone, 0) if zone else 0


def _order_can_go_to_agent(
    order: Order,
    agent: Agent,
    warehouse: Warehouse,
    products_by_id: Dict[str, Product],
) -> bool:
    """True si la commande peut être assignée à l'agent (zones, fragile, poids max)."""
    restrictions = agent.restrictions
    no_zones = set(restrictions.get("no_zones", []))
    no_fragile = restrictions.get("no_fragile", False)
    max_item_weight = restrictions.get("max_item_weight", 0.0)

    for loc in order.unique_locations:
        zone = get_product_zone(warehouse, loc)
        if zone and zone in no_zones:
            return False

    if no_fragile:
        for item in order.items:
            product = products_by_id.get(item.product_id)
            if product and getattr(product, "fragile", False):
                return False

    if max_item_weight > 0:
        for item in order.items:
            product = products_by_id.get(item.product_id)
            if product and product.weight > max_item_weight:
                return False

    return True


def _build_incompatible_pairs(
    orders: List[Order],
    products_by_id: Dict[str, Product],
) -> List[tuple]:
    """Liste de paires (order_idx_1, order_idx_2) d'indices de commandes incompatibles."""
    pairs = []
    for order_idx_1, order_first in enumerate(orders):
        prods_first = [products_by_id[item.product_id] for item in order_first.items if item.product_id in products_by_id]
        for order_idx_2, order_second in enumerate(orders):
            if order_idx_1 >= order_idx_2:
                continue
            prods_second = [products_by_id[item.product_id] for item in order_second.items if item.product_id in products_by_id]
            if not can_combine(prods_first + prods_second):
                pairs.append((order_idx_1, order_idx_2))
    return pairs


def _estimate_order_distance(warehouse: Warehouse, order: Order) -> int:
    entry = warehouse.entry_point
    return sum(entry.manhattan(loc) for loc in order.unique_locations)


def allocate_with_cpsat(
    orders: List[Order],
    agents: List[Agent],
    products_by_id: Dict[str, Product],
    warehouse: Warehouse,
    objective: str = "cost",
    time_limit_seconds: int = 30,
) -> Dict[str, Optional[str]]:
    """
    Allocation par CSP avec OR-Tools CP-SAT.

    Variables : assign[order_i] ∈ {0, 1, ..., n_agents} (0 = non assigné).
    Contraintes : capacité, incompatibilités, restrictions (zones, fragile, poids max).
    Objectif : minimiser coût total ou maximiser nombre assigné.

    Returns:
        {order_id: agent_id or None}
    """
    if not CPSAT_AVAILABLE:
        raise ImportError("OR-Tools CP-SAT non disponible. pip install ortools")

    n_orders = len(orders)
    n_agents = len(agents)
    if n_orders == 0 or n_agents == 0:
        return {order.id: None for order in orders}

    model = cp_model.CpModel()
    scale = 100

    # allowed[order_idx][agent_idx] = True si la commande peut aller à l'agent
    allowed = []
    for order_idx, order in enumerate(orders):
        row = []
        for agent in agents:
            row.append(_order_can_go_to_agent(order, agent, warehouse, products_by_id))
        allowed.append(row)

    # assignment_vars[order_idx][slot] = 1 si commande assignée (slot 0 = non assigné, 1..n_agents = agent)
    assignment_vars = []
    for order_idx in range(n_orders):
        row_vars = []
        for slot in range(n_agents + 1):
            row_vars.append(model.NewBoolVar(f"x_{order_idx}_{slot}"))
        assignment_vars.append(row_vars)

    # Chaque commande est soit non assignée (slot=0) soit assignée à exactement un agent
    for order_idx in range(n_orders):
        model.Add(sum(assignment_vars[order_idx][slot] for slot in range(n_agents + 1)) == 1)

    # Si commande ne peut pas aller à l'agent, variable = 0
    for order_idx in range(n_orders):
        for agent_idx in range(n_agents):
            if not allowed[order_idx][agent_idx]:
                model.Add(assignment_vars[order_idx][agent_idx + 1] == 0)

    # Capacité poids/volume : pour chaque agent, somme des commandes assignées <= cap
    for agent_idx in range(n_agents):
        weight_terms = []
        volume_terms = []
        for order_idx in range(n_orders):
            order_weight_scaled = int(round(orders[order_idx].total_weight * scale))
            order_volume_scaled = int(round(orders[order_idx].total_volume * scale))
            contrib_w = model.NewIntVar(0, order_weight_scaled, f"cw_{order_idx}_{agent_idx}")
            model.AddMultiplicationEquality(contrib_w, [assignment_vars[order_idx][agent_idx + 1], model.NewConstant(order_weight_scaled)])
            weight_terms.append(contrib_w)
            contrib_v = model.NewIntVar(0, order_volume_scaled, f"cv_{order_idx}_{agent_idx}")
            model.AddMultiplicationEquality(contrib_v, [assignment_vars[order_idx][agent_idx + 1], model.NewConstant(order_volume_scaled)])
            volume_terms.append(contrib_v)
        model.Add(sum(weight_terms) <= int(agents[agent_idx].capacity_weight * scale))
        model.Add(sum(volume_terms) <= int(agents[agent_idx].capacity_volume * scale))

    # Incompatibilités : deux commandes incompatibles ne peuvent pas être sur le même agent
    incompatible_pairs = _build_incompatible_pairs(orders, products_by_id)
    for order_idx_1, order_idx_2 in incompatible_pairs:
        for agent_idx in range(n_agents):
            model.Add(assignment_vars[order_idx_1][agent_idx + 1] + assignment_vars[order_idx_2][agent_idx + 1] <= 1)

    # Objectif : coût total (approximation) ou nombre assigné
    if objective == "cost":
        cost_terms = []
        for order_idx in range(n_orders):
            dist = _estimate_order_distance(warehouse, orders[order_idx])
            n_items = sum(item.quantity for item in orders[order_idx].items)
            picking_sec = n_items * 30
            for agent_idx in range(n_agents):
                agent = agents[agent_idx]
                travel_sec = dist / agent.speed if agent.speed > 0 else 0
                total_sec = travel_sec + picking_sec
                cost_cent = int(round(total_sec * agent.cost_per_hour / 36))
                term = model.NewIntVar(0, cost_cent, f"cost_{order_idx}_{agent_idx}")
                model.AddMultiplicationEquality(term, [assignment_vars[order_idx][agent_idx + 1], model.NewConstant(cost_cent)])
                cost_terms.append(term)
        model.Minimize(sum(cost_terms))
    else:
        num_assigned_vars = []
        for order_idx in range(n_orders):
            for slot in range(1, n_agents + 1):
                num_assigned_vars.append(assignment_vars[order_idx][slot])
        model.Maximize(sum(num_assigned_vars))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_seconds)

    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {orders[order_idx].id: None for order_idx in range(n_orders)}

    assignment = {}
    for order_idx in range(n_orders):
        for slot in range(1, n_agents + 1):
            if solver.Value(assignment_vars[order_idx][slot]) == 1:
                assignment[orders[order_idx].id] = agents[slot - 1].id
                break
        else:
            assignment[orders[order_idx].id] = None
    return assignment


def allocate_batches_with_cpsat(
    batches: List,
    agents: List[Agent],
    products_by_id: Dict[str, Product],
    warehouse: Warehouse,
) -> Dict[int, Optional[str]]:
    """
    Alloue les lots aux agents via CP-SAT.
    batches[i].orders = liste des commandes du lot i.
    Returns: {batch_index: agent_id or None}
    """
    if not CPSAT_AVAILABLE or not batches or not agents:
        return {batch_idx: None for batch_idx in range(len(batches))}

    n_batches = len(batches)
    n_agents = len(agents)
    model = cp_model.CpModel()
    scale = 100

    # allowed[batch_idx][agent_idx] = True si le lot peut aller à l'agent
    allowed = []
    for batch_idx, batch in enumerate(batches):
        orders_in_batch = getattr(batch, "orders", [])
        row = []
        for agent in agents:
            ok = all(
                _order_can_go_to_agent(order, agent, warehouse, products_by_id)
                for order in orders_in_batch
            ) if orders_in_batch else True
            row.append(ok)
        allowed.append(row)

    # assignment_vars[batch_idx][slot] : slot 0 = non assigné, 1..n_agents = agent
    assignment_vars = []
    for batch_idx in range(n_batches):
        row_vars = [model.NewBoolVar(f"xb_{batch_idx}_0")]
        for agent_idx in range(n_agents):
            row_vars.append(model.NewBoolVar(f"xb_{batch_idx}_{agent_idx + 1}"))
        assignment_vars.append(row_vars)

    for batch_idx in range(n_batches):
        model.Add(sum(assignment_vars[batch_idx][slot] for slot in range(n_agents + 1)) == 1)

    for batch_idx in range(n_batches):
        for agent_idx in range(n_agents):
            if not allowed[batch_idx][agent_idx]:
                model.Add(assignment_vars[batch_idx][agent_idx + 1] == 0)

    for agent_idx in range(n_agents):
        weight_terms = [model.NewIntVar(0, int(batches[batch_idx].total_weight * scale), f"bw_{batch_idx}_{agent_idx}")
                       for batch_idx in range(n_batches)]
        for batch_idx in range(n_batches):
            batch_weight_scaled = int(round(batches[batch_idx].total_weight * scale))
            model.AddMultiplicationEquality(weight_terms[batch_idx], [assignment_vars[batch_idx][agent_idx + 1], model.NewConstant(batch_weight_scaled)])
        model.Add(sum(weight_terms) <= int(agents[agent_idx].capacity_weight * scale))
        volume_terms = [model.NewIntVar(0, int(batches[batch_idx].total_volume * scale), f"bv_{batch_idx}_{agent_idx}")
                       for batch_idx in range(n_batches)]
        for batch_idx in range(n_batches):
            batch_volume_scaled = int(round(batches[batch_idx].total_volume * scale))
            model.AddMultiplicationEquality(volume_terms[batch_idx], [assignment_vars[batch_idx][agent_idx + 1], model.NewConstant(batch_volume_scaled)])
        model.Add(sum(volume_terms) <= int(agents[agent_idx].capacity_volume * scale))

    model.Maximize(sum(assignment_vars[batch_idx][agent_idx + 1] for batch_idx in range(n_batches) for agent_idx in range(n_agents)))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {batch_idx: None for batch_idx in range(n_batches)}

    result = {}
    for batch_idx in range(n_batches):
        for agent_idx in range(n_agents):
            if solver.Value(assignment_vars[batch_idx][agent_idx + 1]) == 1:
                result[batch_idx] = agents[agent_idx].id
                break
        else:
            result[batch_idx] = None
    return result
