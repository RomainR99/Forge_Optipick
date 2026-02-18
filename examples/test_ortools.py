"""
Script Python utilisant OR-Tools pour résoudre le même problème TSP
Comparable au fichier test.mzn mais avec OR-Tools
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    print("⚠️  OR-Tools n'est pas installé. pip install ortools")


def solve_tsp_ortools(distance_matrix: list[list[int]], depot: int = 0) -> tuple[list[int], int]:
    """
    Résout le TSP avec OR-Tools Routing.
    
    Args:
        distance_matrix: Matrice de distances (n x n)
        depot: Index du point de départ (par défaut 0)
    
    Returns:
        Tuple (chemin, distance_totale)
    """
    if not ORTOOLS_AVAILABLE:
        raise ImportError("OR-Tools n'est pas disponible")
    
    num_locations = len(distance_matrix)
    
    # Créer le gestionnaire de routing
    manager = pywrapcp.RoutingIndexManager(num_locations, 1, depot)
    routing = pywrapcp.RoutingModel(manager)
    
    # Callback pour les distances
    def distance_callback(from_index, to_index):
        """Retourne la distance entre deux nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Paramètres de recherche
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 5
    
    # Résoudre
    solution = routing.SolveWithParameters(search_parameters)
    
    if solution is None:
        raise RuntimeError("Aucune solution trouvée")
    
    # Extraire le chemin
    index = routing.Start(0)
    route = []
    route_distance = 0
    
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        route.append(node)
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    
    # Ajouter le dernier node
    route.append(manager.IndexToNode(index))
    
    return route, route_distance


def main():
    print("=" * 60)
    print("Exemple : TSP avec OR-Tools")
    print("2 agents, 2 commandes, 2 produits")
    print("=" * 60)
    
    # Charger les données JSON
    json_path = Path(__file__).parent / "data_simple.json"
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"\n📋 Données JSON chargées depuis : {json_path.name}")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("\n⚠️  Fichier data_simple.json non trouvé, utilisation des données par défaut")
        data = {
            "agents": [
                {"id": "R1", "type": "robot"},
                {"id": "H1", "type": "human"}
            ],
            "orders": [
                {"id": "Order_001", "items": [{"product_id": "P1"}]},
                {"id": "Order_002", "items": [{"product_id": "P2"}]}
            ],
            "products": [
                {"id": "P1", "location": [2, 0]},
                {"id": "P2", "location": [3, 1]}
            ]
        }
    
    if not ORTOOLS_AVAILABLE:
        print("\n❌ OR-Tools non disponible. Installez-le pour continuer.")
        print("   pip install ortools")
        return
    
    # Matrice de distances (identique à test.mzn)
    distance_matrix = [
        [0, 3, 5, 7],  # Location 0 (entrée) → distances
        [3, 0, 2, 4],  # Location 1 → distances
        [5, 2, 0, 2],  # Location 2 → distances
        [7, 4, 2, 0]   # Location 3 → distances
    ]
    
    print("\n📊 Matrice de distances :")
    print("        Entrée  P1   P2   P4")
    for i, row in enumerate(distance_matrix):
        labels = ["Entrée", "P1", "P2", "P4"]
        print(f"{labels[i]:8} " + "  ".join(f"{d:3}" for d in row))
    
    print("\n⏱️  Résolution avec OR-Tools...")
    
    try:
        route, total_distance = solve_tsp_ortools(distance_matrix, depot=0)
        
        print("\n" + "=" * 60)
        print("✅ RÉSULTAT : Chemin le plus court (OR-Tools)")
        print("=" * 60)
        print("\nDépart : Location 0 (Entrée)")
        print("Chemin optimal :")
        
        # Afficher le chemin
        labels = ["Entrée", "P1", "P2", "P4"]
        path_str = " → ".join(f"{labels[node]}" for node in route)
        print(f"  {path_str}")
        
        # Afficher avec indices numériques aussi
        route_str = " → ".join(str(node) for node in route)
        print(f"\n  (Indices : {route_str})")
        
        print(f"\nDistance totale minimale = {total_distance} unités")
        print("=" * 60)
        
        print("\n📍 Interprétation :")
        print("  Location 0 = Entrée (0, 0) - Point de départ")
        print("  Location 1 = Produit P1 (2, 0)")
        print("  Location 2 = Produit P2 (3, 1)")
        print("  Location 3 = Produit supplémentaire (5, 2)")
        
    except Exception as e:
        print(f"\n❌ Erreur : {e}")


if __name__ == "__main__":
    main()
