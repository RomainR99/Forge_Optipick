"""
Module de vérification des contraintes dures pour le projet OptiPick (Jour 2).
"""
from __future__ import annotations

from typing import Dict, List, Set, Optional

from src.models import (
    Agent,
    Order,
    Product,
    Warehouse,
    Location,
)


def get_product_zone(warehouse: Warehouse, location: Location) -> Optional[str]:
    """
    Détermine à quelle zone appartient une location.
    Retourne le nom de la zone (A, B, C, D, E) ou None si aucune zone ne correspond.
    """
    for zone_name, zone_locations in warehouse.zones.items():
        for zone_loc in zone_locations:
            if zone_loc.x == location.x and zone_loc.y == location.y:
                return zone_name
    return None


def can_combine(products: List[Product]) -> bool:
    """
    2.2) VÉRIFICATION D'INCOMPATIBILITÉS
    Vérifie qu'aucun produit n'est incompatible avec un autre dans la liste.
    Retourne False si deux produits incompatibles sont présents.
    """
    product_ids = {p.id for p in products}
    
    for product in products:
        # Vérifier si ce produit est incompatible avec un autre produit de la liste
        for incompatible_id in product.incompatible_with:
            if incompatible_id in product_ids:
                return False
    
    return True


def check_robot_restrictions(
    agent: Agent,
    order: Order,
    products_by_id: Dict[str, Product],
    warehouse: Warehouse,
    restrictions: Dict
) -> bool:
    """
    2.3) RESTRICTIONS DES ROBOTS
    Vérifie toutes les restrictions spécifiques aux robots :
    - Pas de zone interdite (no_zones)
    - Pas d'objets fragiles (no_fragile)
    - Pas d'objets trop lourds (max_item_weight)
    """
    if agent.type != "robot":
        return True  # Les restrictions ne s'appliquent qu'aux robots
    
    # Vérifier les zones interdites
    no_zones = restrictions.get("no_zones", [])
    if no_zones:
        for location in order.unique_locations:
            zone = get_product_zone(warehouse, location)
            if zone in no_zones:
                return False
    
    # Vérifier les objets fragiles
    if restrictions.get("no_fragile", False):
        for item in order.items:
            product = products_by_id.get(item.product_id)
            if product and product.fragile:
                return False
    
    # Vérifier le poids maximum par item
    max_item_weight = restrictions.get("max_item_weight")
    if max_item_weight is not None:
        for item in order.items:
            product = products_by_id.get(item.product_id)
            if product and product.weight > max_item_weight:
                return False
    
    return True


def check_cart_human_association(
    agent: Agent,
    order: Order,
    agents: List[Agent],
    assignment: Dict[str, Optional[str]]
) -> bool:
    """
    2.4) GESTION DES CHARIOTS
    Vérifie qu'un chariot peut être assigné à une commande.
    Un chariot nécessite qu'un humain soit disponible pour le gérer.
    Pour simplifier Jour 2 : on vérifie qu'il existe au moins un humain disponible
    qui pourrait prendre cette commande (avec ou sans chariot).
    """
    if agent.type != "cart":
        return True  # Cette vérification ne s'applique qu'aux chariots
    
    # Trouver tous les humains disponibles
    humans = [a for a in agents if a.type == "human"]
    
    # Vérifier qu'il existe au moins un humain disponible
    if not humans:
        return False
    
    # Vérifier qu'au moins un humain peut prendre la commande (capacité suffisante)
    # Un humain peut gérer un chariot, donc on vérifie sa capacité directe
    for human in humans:
        if human.can_take(order):
            return True
    
    return False


def can_agent_take_order_with_constraints(
    agent: Agent,
    order: Order,
    products_by_id: Dict[str, Product],
    warehouse: Warehouse,
    restrictions: Dict,
    agents: List[Agent],
    assignment: Dict[str, Optional[str]]
) -> bool:
    """
    Vérifie toutes les contraintes pour déterminer si un agent peut prendre une commande.
    Combine toutes les vérifications :
    1. Capacité (poids/volume) - déjà dans Agent.can_take()
    2. Incompatibilités entre produits
    3. Restrictions des robots
    4. Gestion des chariots
    """
    # 1. Vérification de capacité (déjà implémentée dans Agent.can_take())
    if not agent.can_take(order):
        return False
    
    # 2. Vérification d'incompatibilités
    order_products = [
        products_by_id[item.product_id]
        for item in order.items
        if item.product_id in products_by_id
    ]
    if not can_combine(order_products):
        return False
    
    # 3. Vérification des restrictions robots
    if not check_robot_restrictions(agent, order, products_by_id, warehouse, restrictions):
        return False
    
    # 4. Vérification de l'association chariot-humain
    if not check_cart_human_association(agent, order, agents, assignment):
        return False
    
    return True
