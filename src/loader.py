"""
Chargement et parsing des données JSON pour le projet OptiPick.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List

from models import (
    Warehouse,
    Product,
    Agent,
    Robot,
    Human,
    Cart,
    Order,
    OrderItem,
    Location,
)


def load_json(path: Path) -> dict | list:
    """Charge un fichier JSON et retourne son contenu."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_warehouse(data: dict) -> Warehouse:
    """Parse les données JSON de l'entrepôt."""
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
    """Parse les données JSON des produits."""
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
    """Construit un agent à partir des données JSON."""
    base_kwargs = dict(
        id=raw["id"],
        type=raw.get("type", "unknown"),
        capacity_weight=float(raw.get("capacity_weight", 0.0)),
        capacity_volume=float(raw.get("capacity_volume", 0.0)),
        speed=float(raw.get("speed", 0.0)),
        cost_per_hour=float(raw.get("cost_per_hour", 0.0)),
        restrictions=dict(raw.get("restrictions", {})),  # Charger les restrictions (Jour 2)
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
    """Parse les données JSON des agents."""
    return [build_agent(a) for a in data]


def parse_orders(data: list) -> List[Order]:
    """Parse les données JSON des commandes."""
    orders: List[Order] = []
    for o in data:
        items = [
            OrderItem(product_id=it["product_id"], quantity=int(it["quantity"]))
            for it in o.get("items", [])
        ]
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
