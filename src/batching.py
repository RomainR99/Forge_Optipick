"""
Jour 4 : Regroupement de commandes (batching).
Stratégie : grouper les commandes avec produits proches, même deadline (ou compatibles),
capacité agent suffisante, pas d'incompatibilités.
"""
from __future__ import annotations

from typing import Dict, List, Tuple
from dataclasses import dataclass

from src.models import Order, Agent, Product, Warehouse, Location
from src.constraints import can_combine


@dataclass
class Batch:
    """Un lot = liste de commandes regroupées (traité comme une méta-commande pour l'allocation)."""
    orders: List[Order]
    total_weight: float
    total_volume: float
    unique_locations: List[Location]
    deadline: str  # deadline la plus stricte du lot

    @property
    def order_ids(self) -> List[str]:
        return [order.id for order in self.orders]


def _deadline_to_minutes(deadline: str) -> int:
    h, m = deadline.split(":")
    return int(h) * 60 + int(m)


def _orders_compatible_deadline(orders: List[Order], max_minutes_diff: int = 60) -> bool:
    """True si les deadlines sont dans une fenêtre de max_minutes_diff minutes."""
    if not orders:
        return True
    minutes = [_deadline_to_minutes(order.deadline) for order in orders]
    return max(minutes) - min(minutes) <= max_minutes_diff


def _batch_from_orders(orders: List[Order], products_by_id: Dict[str, Product]) -> Batch:
    """Construit un Batch à partir d'une liste de commandes (poids/volume/locations agrégés)."""
    total_w = sum(order.total_weight for order in orders)
    total_v = sum(order.total_volume for order in orders)
    seen = set()
    locs = []
    for order in orders:
        for loc in order.unique_locations:
            coord_key = (loc.x, loc.y)
            if coord_key not in seen:
                seen.add(coord_key)
                locs.append(loc)
    deadline = min(orders, key=lambda order: _deadline_to_minutes(order.deadline)).deadline
    return Batch(orders=orders, total_weight=total_w, total_volume=total_v, unique_locations=locs, deadline=deadline)


def build_batches(
    orders: List[Order],
    products_by_id: Dict[str, Product],
    max_batch_weight: float,
    max_batch_volume: float,
    deadline_window_minutes: int = 60,
) -> List[Batch]:
    """
    Regroupe les commandes en lots compatibles :
    - même fenêtre de deadline (par défaut 60 min),
    - capacité (poids/volume) du lot <= max_batch_* (ex. capacité max d'un agent),
    - pas d'incompatibilités entre produits dans le lot.

    Stratégie gloutonne : tri par deadline, puis pour chaque commande tenter de l'ajouter
    au premier lot compatible (même fenêtre, capacité, pas d'incompatibilité).
    """
    if not orders:
        return []

    sorted_orders = sorted(orders, key=lambda order: _deadline_to_minutes(order.deadline))
    batches: List[Batch] = []

    for order in sorted_orders:
        placed = False
        prods_order = [products_by_id[item.product_id] for item in order.items if item.product_id in products_by_id]

        for batch in batches:
            if batch.total_weight + order.total_weight > max_batch_weight:
                continue
            if batch.total_volume + order.total_volume > max_batch_volume:
                continue
            batch_deadlines = [ord_in_batch.deadline for ord_in_batch in batch.orders] + [order.deadline]
            batch_mins = [_deadline_to_minutes(deadline_str) for deadline_str in batch_deadlines]
            if max(batch_mins) - min(batch_mins) > deadline_window_minutes:
                continue
            all_prods = []
            for ord_in_batch in batch.orders:
                all_prods.extend(products_by_id[item.product_id] for item in ord_in_batch.items if item.product_id in products_by_id)
            if not can_combine(all_prods + prods_order):
                continue

            batch.orders.append(order)
            batch.total_weight += order.total_weight
            batch.total_volume += order.total_volume
            for loc in order.unique_locations:
                coord_key = (loc.x, loc.y)
                if coord_key not in {(loc_existing.x, loc_existing.y) for loc_existing in batch.unique_locations}:
                    batch.unique_locations.append(loc)
            if _deadline_to_minutes(order.deadline) < _deadline_to_minutes(batch.deadline):
                batch.deadline = order.deadline
            placed = True
            break

        if not placed:
            batches.append(_batch_from_orders([order], products_by_id))

    return batches


def batches_to_assignment(
    batches: List[Batch],
    batch_assignment: Dict[int, str],
) -> Dict[str, str]:
    """
    Convertit une affectation batch_id -> agent_id en order_id -> agent_id.
    batch_assignment : index du batch (0..len(batches)-1) -> agent_id
    """
    assignment = {}
    for batch_idx, batch in enumerate(batches):
        agent_id = batch_assignment.get(batch_idx)
        if agent_id:
            for order in batch.orders:
                assignment[order.id] = agent_id
    return assignment
