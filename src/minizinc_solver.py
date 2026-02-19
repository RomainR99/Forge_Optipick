"""
Interface MiniZinc pour l'allocation optimale (Jour 2).
Charge models/allocation.mzn, construit les paramètres depuis les données Python,
et retourne l'assignment {order_id: agent_id or None}.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from src.models import Agent, Order, Product, Warehouse
from src.constraints import get_product_zone, can_combine

MINIZINC_AVAILABLE = False
_minizinc_checked = False


def check_minizinc_available() -> bool:
    """Vérifie si MiniZinc est installé et utilisable (package Python + exécutable)."""
    global MINIZINC_AVAILABLE, _minizinc_checked
    if _minizinc_checked:
        return MINIZINC_AVAILABLE
    _minizinc_checked = True
    try:
        from minizinc import default_driver
        if default_driver is None:
            return False
        MINIZINC_AVAILABLE = True
        return True
    except Exception:
        return False


def _zone_to_int(zone: Optional[str]) -> int:
    zone_map = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
    return zone_map.get(zone, 0) if zone else 0


def _build_incompatible_matrix(
    orders: List[Order],
    products_by_id: Dict[str, Product],
) -> List[List[bool]]:
    """Matrice n_orders x n_orders : incompatible[i][j] = True si commandes i et j incompatibles."""
    n = len(orders)
    mat = [[False] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            prods_i = [products_by_id[it.product_id] for it in orders[i].items if it.product_id in products_by_id]
            prods_j = [products_by_id[it.product_id] for it in orders[j].items if it.product_id in products_by_id]
            if not can_combine(prods_i + prods_j):
                mat[i][j] = True
                mat[j][i] = True
    return mat


def allocate_with_minizinc(
    orders: List[Order],
    agents: List[Agent],
    products_by_id: Dict[str, Product],
    warehouse: Warehouse,
    solver_name: str = "cbc",
) -> Dict[str, Optional[str]]:
    """
    Allocation optimale avec MiniZinc (modèle allocation.mzn).
    Maximise le nombre de commandes assignées sous les contraintes.

    Returns:
        {order_id: agent_id or None}
    """
    if not check_minizinc_available():
        raise RuntimeError(
            "MiniZinc non disponible. Installez : 1) MiniZinc depuis https://www.minizinc.org/ "
            "2) pip install minizinc"
        )

    from minizinc import Instance, Model, Solver

    n_orders = len(orders)
    n_agents = len(agents)
    if n_orders == 0 or n_agents == 0:
        return {o.id: None for o in orders}

    model_path = Path(__file__).parent.parent / "models" / "allocation.mzn"
    model = Model(str(model_path))
    solver = Solver.lookup(solver_name)
    instance = Instance(solver, model)

    instance["n_orders"] = n_orders
    instance["n_agents"] = n_agents
    instance["capacity_weight"] = [a.capacity_weight for a in agents]
    instance["capacity_volume"] = [a.capacity_volume for a in agents]
    agent_type_map = {"robot": 0, "human": 1, "cart": 2}
    instance["agent_type"] = [agent_type_map.get(a.type, 0) for a in agents]
    instance["order_weight"] = [o.total_weight for o in orders]
    instance["order_volume"] = [o.total_volume for o in orders]

    no_zones_map = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
    forbidden_zones = []
    for agent in agents:
        no_zones = set(agent.restrictions.get("no_zones", []))
        row = [False] * 5
        for z in no_zones:
            idx = no_zones_map.get(z)
            if idx is not None:
                row[idx] = True
        forbidden_zones.append(row)
    instance["forbidden_zones"] = forbidden_zones

    instance["no_fragile"] = [agent.restrictions.get("no_fragile", False) for agent in agents]
    instance["max_item_weight"] = [float(agent.restrictions.get("max_item_weight", 0) or 0) for agent in agents]

    order_zones = []
    order_has_fragile = []
    order_max_item_weight = []
    order_has_high_level = []
    for order in orders:
        zone_int = 0
        has_fragile = False
        max_w = 0.0
        has_high = False
        for item in order.items:
            prod = products_by_id.get(item.product_id)
            if prod:
                loc = prod.location
                zn = get_product_zone(warehouse, loc)
                zone_int = _zone_to_int(zn) if zn else 0
                if getattr(prod, "fragile", False):
                    has_fragile = True
                if prod.weight > max_w:
                    max_w = prod.weight
                # Extension 1 : niveau 3-5 = hauteur inaccessible aux robots
                level = getattr(prod, "level", 1)
                if level >= 3:
                    has_high = True
        order_zones.append(zone_int)
        order_has_fragile.append(has_fragile)
        order_max_item_weight.append(max_w)
        order_has_high_level.append(has_high)
    instance["order_zones"] = order_zones
    instance["order_has_fragile"] = order_has_fragile
    instance["order_max_item_weight"] = order_max_item_weight
    instance["order_has_high_level"] = order_has_high_level

    # EXTENSION 2 : Commandes express (par défaut toutes standard)
    instance["order_is_express"] = [
        getattr(order, "priority", "standard") == "express" 
        for order in orders
    ]

    # EXTENSION 3 : Agents disponibles (par défaut tous disponibles)
    instance["agent_available"] = [True] * n_agents
    
    # EXTENSION 3 : Commandes disponibles (par défaut toutes disponibles)
    instance["order_available"] = [True] * n_orders

    # EXTENSION 4 : Zones congestionnées (par défaut pas de congestion)
    instance["zone_congestion_penalty"] = [0.0] * 5  # Pas de pénalité par défaut
    instance["zone_speed_factor"] = [1.0] * 5  # Vitesse normale par défaut

    # EXTENSION 5 : Scores de préférence RL (par défaut tous à 0.0 = pas de préférence)
    # Matrice n_orders × n_agents : scores de préférence appris par RL
    # Si un modèle RL est disponible, ces scores peuvent être remplis avec les préférences apprises
    instance["rl_preference_scores"] = [[0.0] * n_agents for _ in range(n_orders)]

    instance["incompatible"] = _build_incompatible_matrix(orders, products_by_id)

    result = instance.solve()
    if result is None:
        return {o.id: None for o in orders}

    assign_arr = result["assignment"]
    if hasattr(assign_arr, "__iter__") and not isinstance(assign_arr, (str, dict)):
        assign_list = list(assign_arr)
    else:
        assign_list = [assign_arr]

    assignment = {}
    for i, order in enumerate(orders):
        idx = i if i < len(assign_list) else 0
        val = assign_list[idx] if idx < len(assign_list) else 0
        if val and 1 <= val <= n_agents:
            assignment[order.id] = agents[val - 1].id
        else:
            assignment[order.id] = None

    return assignment
