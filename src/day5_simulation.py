"""
Jour 5.3 : Simulation avant/après réorganisation du stockage.
- Génère 50 commandes test (ou utilise un échantillon)
- Simule avec stockage actuel
- Simule avec stockage optimisé
- Compare les performances (distance, temps, coût)
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional, Any

from src.models import Order, Warehouse, Product, Agent
from src.loader import parse_agents
from src.day5_patterns import run_pattern_analysis
from src.day5_storage import compute_optimized_placement, build_optimized_products


def _clone_agents(agents: List[Agent]) -> List[Agent]:
    """Retourne une copie fraîche des agents (sans affectations)."""
    return parse_agents([
        {
            "id": a.id,
            "type": a.type,
            "capacity_weight": a.capacity_weight,
            "capacity_volume": a.capacity_volume,
            "speed": a.speed,
            "cost_per_hour": a.cost_per_hour,
            "restrictions": getattr(a, "restrictions", {}),
        }
        for a in agents
    ])


def _estimate_order_distance(warehouse: Warehouse, order: Order) -> int:
    entry = warehouse.entry_point
    return sum(entry.manhattan(loc) for loc in order.unique_locations)


def _enrich_orders(orders: List[Order], products_by_id: Dict[str, Product]) -> None:
    for order in orders:
        total_w = 0.0
        total_v = 0.0
        seen: set[tuple[int, int]] = set()
        locs: List[Any] = []
        for item in order.items:
            product = products_by_id.get(item.product_id)
            if product:
                total_w += product.weight * item.quantity
                total_v += product.volume * item.quantity
                key = (product.location.x, product.location.y)
                if key not in seen:
                    seen.add(key)
                    locs.append(product.location)
        order.total_weight = total_w
        order.total_volume = total_v
        order.unique_locations = locs


def generate_test_orders(
    products_by_id: Dict[str, Product],
    n_orders: int = 50,
    min_items: int = 1,
    max_items: int = 5,
    seed: Optional[int] = None,
) -> List[Order]:
    """Génère n_orders commandes aléatoires (échantillonnage parmi les produits)."""
    from src.models import Order, OrderItem

    if seed is not None:
        random.seed(seed)
    product_ids = list(products_by_id.keys())
    if not product_ids:
        return []

    orders = []
    for i in range(n_orders):
        n_items = random.randint(min_items, max_items)
        chosen = random.sample(product_ids, min(n_items, len(product_ids)))
        items = []
        seen_pid: set[str] = set()
        for pid in chosen:
            if pid in seen_pid:
                continue
            seen_pid.add(pid)
            qty = random.randint(1, 3)
            items.append(OrderItem(product_id=pid, quantity=qty))
        if not items:
            items.append(OrderItem(product_id=random.choice(product_ids), quantity=1))
        orders.append(
            Order(
                id=f"Sim_Order_{i+1:03d}",
                received_time="09:00",
                deadline="12:00",
                priority="standard",
                items=items,
            )
        )
    return orders


def run_simulation(
    warehouse: Warehouse,
    orders: List[Order],
    agents: List[Agent],
    products_current: Dict[str, Product],
    products_optimized: Dict[str, Product],
    allocate_fn,
) -> Dict[str, Any]:
    """
    Exécute la simulation avec stockage actuel puis optimisé.
    allocate_fn(orders, agents) -> assignment dict.
    Les distances dépendent des emplacements produits (enrichis avant chaque run).
    """
    # Enrichir avec stockage actuel
    _enrich_orders(orders, products_current)
    agents1 = _clone_agents(agents)
    assign_current = allocate_fn(orders, agents1)
    dist_current = sum(_estimate_order_distance(warehouse, order) for order in orders)

    # Ré-enrichir avec stockage optimisé (mêmes commandes, autres emplacements)
    _enrich_orders(orders, products_optimized)
    agents2 = _clone_agents(agents)
    assign_optimized = allocate_fn(orders, agents2)
    dist_optimized = sum(_estimate_order_distance(warehouse, order) for order in orders)

    n = len(orders)
    n_assigned_current = sum(1 for a in assign_current.values() if a is not None)
    n_assigned_opt = sum(1 for a in assign_optimized.values() if a is not None)

    reduction = 0.0
    if dist_current > 0:
        reduction = (dist_current - dist_optimized) / dist_current * 100

    return {
        "n_orders": n,
        "distance_current": dist_current,
        "distance_optimized": dist_optimized,
        "reduction_percent": round(reduction, 2),
        "n_assigned_current": n_assigned_current,
        "n_assigned_optimized": n_assigned_opt,
    }


def run_before_after(
    warehouse: Warehouse,
    orders_historical: List[Order],
    agents: List[Agent],
    products_by_id: Dict[str, Product],
    n_test_orders: int = 50,
    seed: int = 42,
):
    """
    Pipeline complet : calcule le placement optimisé, génère 50 commandes test,
    simule avant/après et retourne les métriques + placement.
    """
    placement = compute_optimized_placement(
        orders_historical, products_by_id, warehouse
    )
    products_optimized = build_optimized_products(products_by_id, placement)
    test_orders = generate_test_orders(
        products_by_id, n_orders=n_test_orders, seed=seed
    )

    try:
        from main import allocate_first_fit
        alloc = allocate_first_fit
    except Exception:
        from src.allocation_cpsat import allocate_with_cpsat
        def alloc(orders, ags):
            return allocate_with_cpsat(orders, ags, products_by_id, warehouse, objective="assign")
    metrics = run_simulation(
        warehouse,
        test_orders,
        agents,
        products_by_id,
        products_optimized,
        alloc,
    )
    return {
        "placement": placement,
        "products_optimized": products_optimized,
        "metrics": metrics,
        "test_orders": test_orders,
    }
