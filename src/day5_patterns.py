"""
Jour 5.1 : Analyse des patterns de commandes (historique).
- Produits les plus commandés
- Paires de produits souvent commandées ensemble
- Zones les plus visitées
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple, Any

from src.models import Order, Product, Warehouse
from src.constraints import get_product_zone


def product_frequency(orders: List[Order]) -> Dict[str, int]:
    """Compte le nombre de commandes dans lesquelles chaque produit apparaît."""
    count: Dict[str, int] = defaultdict(int)
    for order in orders:
        seen: set[str] = set()
        for item in order.items:
            seen.add(item.product_id)
        for pid in seen:
            count[pid] += 1
    return dict(count)


def top_products(orders: List[Order], n: int = 20) -> List[Tuple[str, int]]:
    """Retourne les n produits les plus commandés (product_id, nb_commandes)."""
    freq = product_frequency(orders)
    sorted_items = sorted(freq.items(), key=lambda x: -x[1])
    return sorted_items[:n]


def co_ordered_pairs(orders: List[Order]) -> Dict[Tuple[str, str], int]:
    """Pour chaque paire de produits commandés ensemble, compte le nombre de commandes."""
    pair_count: Dict[Tuple[str, str], int] = defaultdict(int)
    for order in orders:
        pids = sorted(set(item.product_id for item in order.items))
        for i in range(len(pids)):
            for j in range(i + 1, len(pids)):
                pair_count[(pids[i], pids[j])] += 1
    return dict(pair_count)


def top_co_ordered_pairs(orders: List[Order], n: int = 20) -> List[Tuple[Tuple[str, str], int]]:
    """Retourne les n paires les plus souvent commandées ensemble."""
    pairs = co_ordered_pairs(orders)
    sorted_pairs = sorted(pairs.items(), key=lambda x: -x[1])
    return sorted_pairs[:n]


def zone_visits(
    orders: List[Order],
    products_by_id: Dict[str, Product],
    warehouse: Warehouse,
) -> Dict[str, int]:
    """Compte combien de fois chaque zone est visitée (une commande peut visiter une zone une fois)."""
    zone_count: Dict[str, int] = defaultdict(int)
    for order in orders:
        zones_in_order: set[str] = set()
        for item in order.items:
            product = products_by_id.get(item.product_id)
            if product:
                z = get_product_zone(warehouse, product.location)
                if z:
                    zones_in_order.add(z)
        for z in zones_in_order:
            zone_count[z] += 1
    return dict(zone_count)


def run_pattern_analysis(
    orders: List[Order],
    products_by_id: Dict[str, Product],
    warehouse: Warehouse,
    top_n: int = 20,
) -> Dict[str, Any]:
    """
    Lance l'analyse des patterns et retourne un dictionnaire avec tous les résultats.
    """
    freq = product_frequency(orders)
    top_p = top_products(orders, n=top_n)
    pairs = co_ordered_pairs(orders)
    top_pairs = top_co_ordered_pairs(orders, n=top_n)
    zones = zone_visits(orders, products_by_id, warehouse)

    return {
        "product_frequency": freq,
        "top_products": [(pid, count) for pid, count in top_p],
        "co_ordered_pairs": pairs,
        "top_co_ordered_pairs": [((p1, p2), c) for (p1, p2), c in top_pairs],
        "zone_visits": zones,
        "n_orders": len(orders),
    }
