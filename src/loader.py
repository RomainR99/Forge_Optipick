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
    with path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def parse_warehouse(data: dict) -> Warehouse:
    """Parse les données JSON de l'entrepôt."""
    width = data["dimensions"]["width"]
    height = data["dimensions"]["height"]

    zones: Dict[str, List[Location]] = {}
    for zone_name, zone_info in data.get("zones", {}).items():
        coords = zone_info.get("coords", [])
        zones[zone_name] = [Location(x=coord[0], y=coord[1]) for coord in coords]

    entry = data.get("entry_point", [0, 0])
    entry_point = Location(x=entry[0], y=entry[1])

    return Warehouse(width=width, height=height, zones=zones, entry_point=entry_point)


def parse_products(data: list) -> Dict[str, Product]:
    """Parse les données JSON des produits."""
    products: Dict[str, Product] = {}
    for product_data in data:
        product_id = product_data["id"]
        location_coords = product_data.get("location", [0, 0])
        products[product_id] = Product(
            id=product_id,
            name=product_data.get("name", product_id),
            category=product_data.get("category", "unknown"),
            weight=float(product_data.get("weight", 0.0)),
            volume=float(product_data.get("volume", 0.0)),
            location=Location(location_coords[0], location_coords[1]),
            frequency=product_data.get("frequency", "unknown"),
            fragile=bool(product_data.get("fragile", False)),
            incompatible_with=list(product_data.get("incompatible_with", [])),
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
    agent_type = base_kwargs["type"]
    if agent_type == "robot":
        return Robot(**base_kwargs)
    if agent_type == "human":
        return Human(**base_kwargs)
    if agent_type == "cart":
        return Cart(**base_kwargs)
    return Agent(**base_kwargs)


def parse_agents(data: list) -> List[Agent]:
    """Parse les données JSON des agents."""
    return [build_agent(agent_data) for agent_data in data]


def parse_orders(data: list) -> List[Order]:
    """Parse les données JSON des commandes."""
    orders: List[Order] = []
    for order_data in data:
        items = [
            OrderItem(product_id=item_data["product_id"], quantity=int(item_data["quantity"]))
            for item_data in order_data.get("items", [])
        ]
        orders.append(
            Order(
                id=order_data["id"],
                received_time=order_data.get("received_time", "00:00"),
                deadline=order_data.get("deadline", "23:59"),
                priority=order_data.get("priority", "standard"),
                items=items,
            )
        )
    return orders
