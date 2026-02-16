"""
Classes Warehouse, Product, Agent, Order pour le projet OptiPick.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


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
