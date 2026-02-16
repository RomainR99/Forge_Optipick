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
    id: str                    # Identifiant unique (ex: "R1", "H1", "C1")
    type: str                 # Type d'agent : "robot", "human" ou "cart"
    capacity_weight: float    # Capacité maximale en poids (kg)
    capacity_volume: float   # Capacité maximale en volume (dm³)
    speed: float             # Vitesse de déplacement (m/s)
    cost_per_hour: float     # Coût d'utilisation par heure (€)

    # Attributs d'Affectation (Jour 1)
    assigned_orders: List[str] = field(default_factory=list) #liste des IDs des commandes assignées à cet agent
    #field(default_factory=list) : initialise une nouvelle liste vide pour chaque instance
    used_weight: float = 0.0 # poids total actuellement transporté (kg)
    used_volume: float = 0.0 # volume total actuellement transporté (dm³)

    # Ces valeurs sont mises à jour lors de l'assignation de commandes.

    # Vérifie si l'agent peut prendre une commande.
    def can_take(self, order: Order) -> bool: # Retourne True si les deux conditions sont vraies, sinon False
        return (
            self.used_weight + order.total_weight <= self.capacity_weight # Condition poids
            and self.used_volume + order.total_volume <= self.capacity_volume # Condition volume 
        )
    # Assigne une commande à l'agent et met à jour les compteurs.
    def assign(self, order: Order) -> None:
        self.assigned_orders.append(order.id) # Ajoute l'ID de la commande à assigned_orders
        self.used_weight += order.total_weight # Ajoute le poids de la commande à used_weight
        self.used_volume += order.total_volume # Ajoute le volume de la commande à used_volume


# Sous-classes (Jour 1 : identiques à Agent, mais utiles pour la suite)
class Robot(Agent):
    pass


class Human(Agent):
    pass


class Cart(Agent):
    pass
