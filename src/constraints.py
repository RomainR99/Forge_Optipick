"""
Vérification des contraintes pour le projet OptiPick.
Jour 2 : Contraintes dures (capacité, incompatibilités, restrictions robots, chariots)
"""
from __future__ import annotations

from typing import List, Optional
from src.models import Warehouse, Location, Product, Agent, Order


def get_product_zone(warehouse: Warehouse, location: Location) -> Optional[str]:
    """
    Détermine la zone (A, B, C, D, E) d'un emplacement donné.
    
    Args:
        warehouse: Configuration de l'entrepôt avec les zones
        location: Emplacement à vérifier
    
    Returns:
        Nom de la zone (A, B, C, D, E) ou None si l'emplacement n'est dans aucune zone
    """
    for zone_name, zone_locations in warehouse.zones.items():
        if location in zone_locations:
            return zone_name
    return None


def can_combine(products: List[Product]) -> bool:
    """
    Vérifie si une liste de produits peut être combinée (pas d'incompatibilités).
    
    Args:
        products: Liste des produits à vérifier
    
    Returns:
        True si tous les produits sont compatibles entre eux, False sinon
    """
    # Pour chaque paire de produits
    for i, product_first in enumerate(products):
        for j, product_second in enumerate(products):
            if i < j:  # Éviter les doublons et les comparaisons avec soi-même
                # Vérifier si product_first est incompatible avec product_second
                if product_second.id in product_first.incompatible_with:
                    return False
                # Vérifier si product_second est incompatible avec product_first
                if product_first.id in product_second.incompatible_with:
                    return False
    return True
