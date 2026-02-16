"""
Module d'allocation optimale utilisant MiniZinc pour le projet OptiPick.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    from minizinc import Instance, Model, Solver
    MINIZINC_AVAILABLE = True
except ImportError:
    MINIZINC_AVAILABLE = False
    print("⚠️  MiniZinc n'est pas installé. Utilisez: pip install minizinc")

from src.models import (
    Agent,
    Order,
    Product,
    Warehouse,
    Location,
)
from src.constraints import (
    get_product_zone,
    can_combine,
)


def zone_to_int(zone: Optional[str]) -> int:
    """Convertit une zone (A, B, C, D, E) en entier pour MiniZinc."""
    if zone is None:
        return -1
    zone_map = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
    return zone_map.get(zone, -1)


def int_to_zone(zone_int: int) -> Optional[str]:
    """Convertit un entier en zone pour MiniZinc."""
    if zone_int == -1:
        return None
    zone_map = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E"}
    return zone_map.get(zone_int)


def allocate_with_minizinc(
    orders: List[Order],
    agents: List[Agent],
    products_by_id: Dict[str, Product],
    warehouse: Warehouse,
    solver_name: str = "gecode"
) -> Dict[str, Optional[str]]:
    """
    Résout le problème d'allocation en utilisant MiniZinc.
    
    Args:
        orders: Liste des commandes à assigner
        agents: Liste des agents disponibles
        products_by_id: Dictionnaire des produits par ID
        warehouse: Configuration de l'entrepôt
        solver_name: Nom du solveur MiniZinc à utiliser (gecode, chuffed, etc.)
    
    Returns:
        Dictionnaire {order_id: agent_id or None}
    """
    if not MINIZINC_AVAILABLE:
        raise ImportError("MiniZinc n'est pas disponible. Installez-le avec: pip install minizinc")
    
    n_orders = len(orders)
    n_agents = len(agents)
    
    if n_orders == 0 or n_agents == 0:
        return {order.id: None for order in orders}
    
    # Charger le modèle MiniZinc
    model_path = Path(__file__).parent.parent / "models" / "allocation.mzn"
    if not model_path.exists():
        raise FileNotFoundError(f"Modèle MiniZinc introuvable: {model_path}")
    
    model = Model(str(model_path))
    
    # Obtenir le solveur
    try:
        solver = Solver.lookup(solver_name)
    except Exception as e:
        print(f"⚠️  Solveur {solver_name} non trouvé, utilisation de 'gecode' par défaut")
        solver = Solver.lookup("gecode")
    
    # Créer une instance
    instance = Instance(solver, model)
    
    # Préparer les données pour MiniZinc
    
    # 1. Capacités des agents
    capacity_weight = [agent.capacity_weight for agent in agents]
    capacity_volume = [agent.capacity_volume for agent in agents]
    agent_type = [0 if agent.type == "robot" else (1 if agent.type == "human" else 2) for agent in agents]
    
    # 2. Poids et volumes des commandes
    order_weight = [order.total_weight for order in orders]
    order_volume = [order.total_volume for order in orders]
    
    # 3. Zones des commandes
    order_zones = []
    order_has_fragile = []
    order_max_item_weight = []
    
    for order in orders:
        # Déterminer la zone (prendre la première zone trouvée, ou -1 si aucune)
        zone = None
        for location in order.unique_locations:
            product_zone = get_product_zone(warehouse, location)
            if product_zone is not None:
                zone = product_zone
                break
        order_zones.append(zone_to_int(zone))
        
        # Vérifier si la commande contient des objets fragiles
        has_fragile = any(
            products_by_id.get(item.product_id, Product("", "", "", 0, 0, Location(0, 0))).fragile
            for item in order.items
        )
        order_has_fragile.append(has_fragile)
        
        # Poids maximum d'un item dans la commande
        max_item_w = max(
            (products_by_id.get(item.product_id, Product("", "", "", 0, 0, Location(0, 0))).weight
             for item in order.items),
            default=0.0
        )
        order_max_item_weight.append(max_item_w)
    
    # 4. Restrictions des robots
    # Matrice [agent, zone] : true si zone interdite pour cet agent
    forbidden_zones_matrix = []
    no_fragile_list = []
    max_item_weight_list = []
    
    for agent in agents:
        restrictions = agent.restrictions
        # Zones interdites : créer une liste de booléens pour chaque zone (0-4)
        no_zones = restrictions.get("no_zones", [])
        forbidden_for_agent = [False] * 5  # 5 zones possibles (A, B, C, D, E)
        for zone_name in no_zones:
            zone_int = zone_to_int(zone_name)
            if 0 <= zone_int < 5:
                forbidden_for_agent[zone_int] = True
        forbidden_zones_matrix.append(forbidden_for_agent)
        
        # Pas d'objets fragiles
        no_fragile_list.append(restrictions.get("no_fragile", False))
        
        # Poids max par item
        max_item_weight_list.append(restrictions.get("max_item_weight", 0.0))
    
    # 5. Matrice d'incompatibilités
    incompatible_matrix = []
    for order_index_1, order_first in enumerate(orders):
        row = []
        products_first = [products_by_id[item.product_id] for item in order_first.items if item.product_id in products_by_id]
        for order_index_2, order_second in enumerate(orders):
            if order_index_1 == order_index_2:
                row.append(False)
            else:
                products_second = [products_by_id[item.product_id] for item in order_second.items if item.product_id in products_by_id]
                # Vérifier si les produits sont incompatibles
                all_products = products_first + products_second
                orders_incompatible = not can_combine(all_products)
                row.append(orders_incompatible)
        incompatible_matrix.append(row)
    
    # Assigner les paramètres à l'instance MiniZinc
    instance["n_orders"] = n_orders
    instance["n_agents"] = n_agents
    instance["capacity_weight"] = capacity_weight
    instance["capacity_volume"] = capacity_volume
    instance["agent_type"] = agent_type
    instance["order_weight"] = order_weight
    instance["order_volume"] = order_volume
    instance["order_zones"] = order_zones
    instance["order_has_fragile"] = order_has_fragile
    instance["order_max_item_weight"] = order_max_item_weight
    instance["forbidden_zones"] = forbidden_zones_matrix
    instance["no_fragile"] = no_fragile_list
    instance["max_item_weight"] = max_item_weight_list
    instance["incompatible"] = incompatible_matrix
    
    # Résoudre
    try:
        result = instance.solve()
        assignment_array = result["assignment"]
    except Exception as e:
        print(f"❌ Erreur lors de la résolution MiniZinc: {e}")
        # Retourner une solution vide en cas d'erreur
        return {order.id: None for order in orders}
    
    # Convertir le résultat en dictionnaire
    assignment = {}
    for order_index, order in enumerate(orders):
        agent_index_minizinc = assignment_array[order_index]
        if agent_index_minizinc == 0:
            assignment[order.id] = None
        else:
            # agent_index_minizinc est 1-indexed dans MiniZinc, notre liste est 0-indexed
            agent_index_python = agent_index_minizinc - 1
            if 0 <= agent_index_python < len(agents):
                assignment[order.id] = agents[agent_index_python].id
            else:
                assignment[order.id] = None
    
    # Mettre à jour les agents avec les assignations
    for order_index, order in enumerate(orders):
        agent_index_minizinc = assignment_array[order_index]
        if agent_index_minizinc != 0:
            agent_index_python = agent_index_minizinc - 1
            if 0 <= agent_index_python < len(agents):
                agents[agent_index_python].assign(order)
    
    return assignment


def check_minizinc_available() -> bool:
    """Vérifie si MiniZinc est disponible."""
    return MINIZINC_AVAILABLE
