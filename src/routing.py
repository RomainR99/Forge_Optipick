"""

Optimisation des tournées (TSP) avec OR-Tools Routing.
Jour 3 : Calcul de tournées optimales pour chaque agent.
"""
from __future__ import annotations

from typing import List, Tuple, Optional

try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

from src.models import Location, Warehouse, Agent, Order, Product


def create_distance_matrix(locations: List[Location]) -> List[List[int]]:
    """
    Crée une matrice de distances Manhattan entre toutes les paires d'emplacements.
    
    Args:
        locations: Liste des emplacements (incluant l'entrée en premier)
    
    Returns:
        Matrice de distances carrée (n x n) où matrix[i][j] = distance entre locations[i] et locations[j]
    """
    n = len(locations)
    matrix = [[0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = locations[i].manhattan(locations[j])
    
    return matrix


def solve_tsp_with_ortools(
    locations: List[Location],
    entry_point: Location,
    time_limit_seconds: int = 30
) -> Tuple[Optional[List[int]], Optional[int]]:
    """
    Résout le TSP avec OR-Tools Routing pour trouver la tournée optimale.
    
    Args:
        locations: Liste des emplacements à visiter (sans l'entrée)
        entry_point: Point d'entrée (départ et retour)
        time_limit_seconds: Limite de temps pour la résolution (défaut: 30s)
    
    Returns:
        Tuple (tournée, distance_totale) où:
        - tournée: Liste des indices dans l'ordre de visite [0=entrée, ...] ou None si échec
        - distance_totale: Distance totale de la tournée ou None si échec
    """
    if not ORTOOLS_AVAILABLE:
        raise ImportError(
            "OR-Tools n'est pas installé. Installez-le avec: pip install ortools\n"
            "L'optimisation TSP nécessite OR-Tools."
        )
    
    # Si aucun emplacement à visiter, retourner directement à l'entrée
    if not locations:
        return [0], 0
    
    # Construire la liste complète : [entrée, emplacement1, emplacement2, ...]
    all_locations = [entry_point] + locations
    
    # Créer la matrice de distances
    distance_matrix = create_distance_matrix(all_locations)
    num_locations = len(all_locations)
    
    # Créer le gestionnaire de données pour OR-Tools
    manager = pywrapcp.RoutingIndexManager(num_locations, 1, 0)  # 1 véhicule, départ à l'index 0
    
    # Créer le modèle de routage
    routing = pywrapcp.RoutingModel(manager)
    
    def distance_callback(from_index: int, to_index: int) -> int:
        """Callback pour calculer la distance entre deux nœuds."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    
    # Définir le coût de chaque arc
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Paramètres de recherche
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = time_limit_seconds
    
    # Résoudre le problème
    solution = routing.SolveWithParameters(search_parameters)
    
    if solution is None:
        return None, None
    
    # Extraire la tournée
    tour = []
    index = routing.Start(0)
    total_distance = 0
    
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        tour.append(node)
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        total_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    
    # Ajouter le retour à l'entrée
    tour.append(0)  # Retour à l'entrée
    
    return tour, total_distance


def compute_route_for_agent(
    agent: Agent,
    assigned_orders: List[Order],
    warehouse: Warehouse,
    products_by_id: dict[str, Product]
) -> Tuple[Optional[List[Location]], Optional[int], Optional[float]]:
    """
    Calcule la tournée optimale pour un agent avec ses commandes assignées.
    
    Args:
        agent: Agent pour lequel calculer la tournée
        assigned_orders: Liste des commandes assignées à cet agent
        warehouse: Objet Warehouse contenant l'entrée
        products_by_id: Dictionnaire des produits par ID
    
    Returns:
        Tuple (tournée_locations, distance_totale, temps_tournée) où:
        - tournée_locations: Liste des emplacements dans l'ordre optimal ou None
        - distance_totale: Distance totale en unités ou None
        - temps_tournée: Temps total en secondes ou None
    """
    # Extraire tous les emplacements uniques des commandes assignées
    unique_locations: List[Location] = []
    seen: set[Tuple[int, int]] = set()
    
    for order in assigned_orders:
        for item in order.items:
            product = products_by_id.get(item.product_id)
            if product:
                key = (product.location.x, product.location.y)
                if key not in seen:
                    seen.add(key)
                    unique_locations.append(product.location)
    
    # Résoudre le TSP
    tour, distance = solve_tsp_with_ortools(unique_locations, warehouse.entry_point)
    
    if tour is None or distance is None:
        return None, None, None
    
    # Convertir les indices de la tournée en emplacements réels
    all_locations = [warehouse.entry_point] + unique_locations
    route_locations = [all_locations[node_idx] for node_idx in tour]
    
    # Calculer le temps de tournée
    # Temps = distance_totale / vitesse + temps de ramassage
    # Vitesse en m/s, distance en unités (on suppose 1 unité = 1 mètre)
    # Temps de ramassage : 30 secondes par produit (selon l'énoncé)
    total_items = sum(len(order.items) for order in assigned_orders)
    picking_time = total_items * 30  # 30 secondes par produit
    
    # Distance en mètres, vitesse en m/s
    travel_time = distance / agent.speed if agent.speed > 0 else 0
    total_time = travel_time + picking_time
    
    return route_locations, distance, total_time


def check_deadlines(
    agent: Agent,
    assigned_orders: List[Order],
    route_time: float,
    current_time: float = 0.0
) -> Tuple[bool, List[str]]:
    """
    Vérifie si toutes les deadlines sont respectées pour les commandes assignées.
    
    Args:
        agent: Agent concerné
        assigned_orders: Liste des commandes assignées
        route_time: Temps total de la tournée en secondes
        current_time: Temps actuel en secondes depuis minuit (défaut: 0)
    
    Returns:
        Tuple (toutes_respectées, commandes_en_retard) où:
        - toutes_respectées: True si toutes les deadlines sont respectées
        - commandes_en_retard: Liste des IDs des commandes en retard
    """
    def time_to_seconds(time_str: str) -> int:
        """Convertit une heure HH:MM en secondes depuis minuit."""
        parts = time_str.split(":")
        return int(parts[0]) * 3600 + int(parts[1]) * 60
    
    finish_time = current_time + route_time
    late_orders = []
    
    for order in assigned_orders:
        deadline_seconds = time_to_seconds(order.deadline)
        if finish_time > deadline_seconds:
            late_orders.append(order.id)
    
    return len(late_orders) == 0, late_orders
