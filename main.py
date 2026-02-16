# Point d'entrée du programme
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional


# =========================
# 1) Modèles (Jour 1)
# =========================

@dataclass(frozen=True)
class Location:
    x: int
    y: int

    def manhattan(self, other: "Location") -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)


@dataclass
class Warehouse:
    width: int
    height: int
    zones: Dict[str, List[Location]]
    entry_point: Location


@dataclass
class Product:
    id: str
    name: str
    category: str
    weight: float
    volume: float
    location: Location
    frequency: str = "unknown"
    fragile: bool = False
    incompatible_with: List[str] = field(default_factory=list)


@dataclass
class OrderItem:
    product_id: str
    quantity: int


@dataclass
class Order:
    id: str
    received_time: str
    deadline: str
    priority: str
    items: List[OrderItem]

    # Calculés après chargement
    total_weight: float = 0.0
    total_volume: float = 0.0
    unique_locations: List[Location] = field(default_factory=list)


@dataclass
class Agent:
    id: str
    type: str  # "robot" | "human" | "cart"
    capacity_weight: float
    capacity_volume: float
    speed: float
    cost_per_hour: float

    # Affectation (Jour 1)
    assigned_orders: List[str] = field(default_factory=list)
    used_weight: float = 0.0
    used_volume: float = 0.0

    def can_take(self, order: Order) -> bool:
        return (
            self.used_weight + order.total_weight <= self.capacity_weight
            and self.used_volume + order.total_volume <= self.capacity_volume
        )

    def assign(self, order: Order) -> None:
        self.assigned_orders.append(order.id)
        self.used_weight += order.total_weight
        self.used_volume += order.total_volume


# Sous-classes (Jour 1 : identiques à Agent, mais utiles pour la suite)
class Robot(Agent):
    pass

class Human(Agent):
    pass

class Cart(Agent):
    pass


# =========================
# 2) Chargement des JSON
# =========================

def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_warehouse(data: dict) -> Warehouse:
    width = data["dimensions"]["width"]
    height = data["dimensions"]["height"]

    zones: Dict[str, List[Location]] = {}
    for zname, zinfo in data.get("zones", {}).items():
        coords = zinfo.get("coords", [])
        zones[zname] = [Location(x=c[0], y=c[1]) for c in coords]

    entry = data.get("entry_point", [0, 0])
    entry_point = Location(x=entry[0], y=entry[1])

    return Warehouse(width=width, height=height, zones=zones, entry_point=entry_point)


def parse_products(data: list) -> Dict[str, Product]:
    products: Dict[str, Product] = {}
    for p in data:
        pid = p["id"]
        loc = p.get("location", [0, 0])
        products[pid] = Product(
            id=pid,
            name=p.get("name", pid),
            category=p.get("category", "unknown"),
            weight=float(p.get("weight", 0.0)),
            volume=float(p.get("volume", 0.0)),
            location=Location(loc[0], loc[1]),
            frequency=p.get("frequency", "unknown"),
            fragile=bool(p.get("fragile", False)),
            incompatible_with=list(p.get("incompatible_with", [])),
        )
    return products


def build_agent(raw: dict) -> Agent:
    base_kwargs = dict(
        id=raw["id"],
        type=raw.get("type", "unknown"),
        capacity_weight=float(raw.get("capacity_weight", 0.0)),
        capacity_volume=float(raw.get("capacity_volume", 0.0)),
        speed=float(raw.get("speed", 0.0)),
        cost_per_hour=float(raw.get("cost_per_hour", 0.0)),
    )
    t = base_kwargs["type"]
    if t == "robot":
        return Robot(**base_kwargs)
    if t == "human":
        return Human(**base_kwargs)
    if t == "cart":
        return Cart(**base_kwargs)
    return Agent(**base_kwargs)


def parse_agents(data: list) -> List[Agent]:
    return [build_agent(a) for a in data]


def parse_orders(data: list) -> List[Order]:
    orders: List[Order] = []
    for o in data:
        items = [OrderItem(product_id=it["product_id"], quantity=int(it["quantity"])) for it in o.get("items", [])]
        orders.append(
            Order(
                id=o["id"],
                received_time=o.get("received_time", "00:00"),
                deadline=o.get("deadline", "23:59"),
                priority=o.get("priority", "standard"),
                items=items,
            )
        )
    return orders


# =========================
# 3) Enrichissement Orders (poids/volume/locations)
# =========================

def enrich_orders(orders: List[Order], products_by_id: Dict[str, Product]) -> None:
    for order in orders:
        total_w = 0.0
        total_v = 0.0
        locs: List[Location] = []
        seen: set[Tuple[int, int]] = set()

        for it in order.items:
            p = products_by_id.get(it.product_id)
            if p is None:
                raise KeyError(f"Produit introuvable: {it.product_id} (dans {order.id})")

            total_w += p.weight * it.quantity
            total_v += p.volume * it.quantity

            key = (p.location.x, p.location.y)
            if key not in seen:
                seen.add(key)
                locs.append(p.location)

        order.total_weight = total_w
        order.total_volume = total_v
        order.unique_locations = locs


# =========================
# 4) Allocation naïve First-Fit
# =========================

def sort_orders_by_received_time(orders: List[Order]) -> List[Order]:
    # "HH:MM" -> minutes
    def to_minutes(hhmm: str) -> int:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    return sorted(orders, key=lambda o: to_minutes(o.received_time))


def allocate_first_fit(orders: List[Order], agents: List[Agent]) -> Dict[str, Optional[str]]:
    """
    Retourne: {order_id: agent_id or None}
    """
    assignment: Dict[str, Optional[str]] = {}

    for order in orders:
        assigned = False
        for agent in agents:
            if agent.can_take(order):
                agent.assign(order)
                assignment[order.id] = agent.id
                assigned = True
                break
        if not assigned:
            assignment[order.id] = None

    return assignment


# =========================
# 5) Distances estimées (Jour 1)
# =========================

def estimate_order_distance(warehouse: Warehouse, order: Order) -> int:
    """
    Estimation simple demandée: somme des distances entrée <-> emplacement.
    (Pas de tournée optimisée, juste un proxy).
    """
    entry = warehouse.entry_point
    return sum(entry.manhattan(loc) for loc in order.unique_locations)


def compute_total_distance(warehouse: Warehouse, orders: List[Order]) -> int:
    return sum(estimate_order_distance(warehouse, o) for o in orders)


# =========================
# 6) Évaluation / affichage
# =========================

def print_report(warehouse: Warehouse, orders: List[Order], agents: List[Agent], assignment: Dict[str, Optional[str]]) -> None:
    total = len(orders)
    assigned = sum(1 for oid, aid in assignment.items() if aid is not None)
    unassigned = total - assigned

    dist_total = compute_total_distance(warehouse, orders)

    print("══════════════════════════════════════")
    print("JOUR 1 — Allocation naïve (First-Fit)")
    print("══════════════════════════════════════")
    print(f"Commandes totales : {total}")
    print(f"Commandes assignées: {assigned}")
    print(f"Commandes non assignées: {unassigned}")
    print(f"Distance totale estimée (proxy): {dist_total}")
    print()

    print("Détail par agent:")
    for a in agents:
        util_w = 0.0 if a.capacity_weight == 0 else (a.used_weight / a.capacity_weight) * 100
        util_v = 0.0 if a.capacity_volume == 0 else (a.used_volume / a.capacity_volume) * 100
        print(f"- {a.id} ({a.type})")
        print(f"  commandes: {len(a.assigned_orders)} -> {a.assigned_orders}")
        print(f"  poids: {a.used_weight:.2f}/{a.capacity_weight:.2f} kg ({util_w:.1f}%)")
        print(f"  volume: {a.used_volume:.2f}/{a.capacity_volume:.2f} dm³ ({util_v:.1f}%)")
    print()

    if unassigned > 0:
        print("Commandes non assignées (capacité insuffisante avec ce First-Fit):")
        for oid, aid in assignment.items():
            if aid is None:
                print(f"- {oid}")
        print()


# =========================
# 7) Main
# =========================

def main(
    warehouse_path: str = "warehouse.json",
    products_path: str = "products.json",
    agents_path: str = "agents.json",
    orders_path: str = "orders.json",
) -> None:
    wh_data = load_json(Path(warehouse_path))
    pr_data = load_json(Path(products_path))
    ag_data = load_json(Path(agents_path))
    or_data = load_json(Path(orders_path))

    warehouse = parse_warehouse(wh_data)
    products_by_id = parse_products(pr_data)
    agents = parse_agents(ag_data)
    orders = parse_orders(or_data)

    enrich_orders(orders, products_by_id)

    orders_sorted = sort_orders_by_received_time(orders)
    assignment = allocate_first_fit(orders_sorted, agents)

    print_report(warehouse, orders_sorted, agents, assignment)


if __name__ == "__main__":
    main()