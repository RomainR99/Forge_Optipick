# Point d'entrée du programme
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Ajouter src au path pour importer les modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models import (
    Location,
    Warehouse,
    Product,
    Order,
    OrderItem,
    Agent,
    Robot,
    Human,
    Cart,
)
from src.loader import (
    load_json,
    parse_warehouse,
    parse_products,
    parse_agents,
    parse_orders,
)
from src.routing import (
    compute_route_for_agent,
    check_deadlines,
)
try:
    from src.minizinc_solver import (
        allocate_with_minizinc,
        check_minizinc_available,
    )
    MINIZINC_AVAILABLE = check_minizinc_available()
except ImportError:
    MINIZINC_AVAILABLE = False


# =========================
# 2) Enrichissement Orders (poids/volume/locations)
# =========================

def enrich_orders(orders: List[Order], products_by_id: Dict[str, Product]) -> None:
    for order in orders:
        total_w = 0.0
        total_v = 0.0
        locs: List[Location] = []
        seen: set[Tuple[int, int]] = set()

        for order_item in order.items:
            product = products_by_id.get(order_item.product_id)
            if product is None:
                raise KeyError(f"Produit introuvable: {order_item.product_id} (dans {order.id})")

            total_w += product.weight * order_item.quantity
            total_v += product.volume * order_item.quantity

            key = (product.location.x, product.location.y)
            if key not in seen:
                seen.add(key)
                locs.append(product.location)

        order.total_weight = total_w
        order.total_volume = total_v
        order.unique_locations = locs


# =========================
# 3) Allocation naïve First-Fit
# =========================


# Tri des commandes par ordre d'arrivée
def sort_orders_by_received_time(orders: List[Order]) -> List[Order]:
    # "HH:MM" -> minutes
    def to_minutes(hhmm: str) -> int:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    return sorted(orders, key=lambda order: to_minutes(order.received_time))
#Convertit l'heure de réception en minutes
#Trie les commandes par ordre chronologique

#Fonction d'allocation First-Fit
def allocate_first_fit(orders: List[Order], agents: List[Agent]) -> Dict[str, Optional[str]]:
    """
    Retourne: {order_id: agent_id or None}
    """
    assignment: Dict[str, Optional[str]] = {}

    for order in orders:  # ← Pour chaque commande (par ordre d'arrivée)
        assigned = False
        for agent in agents:  # ← Parcourt les agents dans l'ordre
            if agent.can_take(order):  # ← Vérifie la capacité suffisante
                agent.assign(order)
                assignment[order.id] = agent.id
                assigned = True
                break  # ← S'arrête au premier agent qui peut prendre la commande
        if not assigned:
            assignment[order.id] = None  # ← Aucun agent disponible

    return assignment


def apply_assignment(
    assignment: Dict[str, Optional[str]],
    orders: List[Order],
    agents: List[Agent],
) -> None:
    """
    Applique un dictionnaire d'assignment (order_id -> agent_id) aux agents :
    appelle agent.assign(order) pour chaque couple, afin que assigned_orders,
    used_weight et used_volume soient à jour (ex. après MiniZinc).
    """
    orders_by_id = {o.id: o for o in orders}
    agents_by_id = {a.id: a for a in agents}
    for order_id, agent_id in assignment.items():
        if agent_id is not None:
            order = orders_by_id.get(order_id)
            agent = agents_by_id.get(agent_id)
            if order and agent:
                agent.assign(order)


# =========================
# 4) Distances estimées (Jour 1)
# =========================

def estimate_order_distance(warehouse: Warehouse, order: Order) -> int:
    """
    Estimation simple demandée: somme des distances entrée <-> emplacement.
    (Pas de tournée optimisée, juste un proxy).
    """
    entry = warehouse.entry_point
    return sum(entry.manhattan(loc) for loc in order.unique_locations)

#Fonction de calcul de la distance totale 
def compute_total_distance(warehouse: Warehouse, orders: List[Order]) -> int:
    return sum(estimate_order_distance(warehouse, order) for order in orders)


# =========================
# 5) Calcul des tournées TSP (Jour 3)
# =========================

def compute_routes_for_all_agents(
    warehouse: Warehouse,
    orders: List[Order],
    agents: List[Agent],
    assignment: Dict[str, Optional[str]],
    products_by_id: Dict[str, Product],
    use_routing: bool = False
) -> Dict[str, Tuple[Optional[List[Location]], Optional[int], Optional[float]]]:
    """
    Calcule les tournées optimales pour tous les agents.
    
    Returns:
        Dictionnaire {agent_id: (route_locations, distance, time)}
    """
    routes: Dict[str, Tuple[Optional[List[Location]], Optional[int], Optional[float]]] = {}
    
    if not use_routing:
        return routes
    
    # Vérifier si OR-Tools est disponible
    try:
        from src.routing import ORTOOLS_AVAILABLE
        if not ORTOOLS_AVAILABLE:
            print("⚠️  OR-Tools n'est pas installé. L'optimisation TSP est désactivée.")
            print("   Installez avec: pip install ortools")
            return routes
    except (ImportError, AttributeError):
        print("⚠️  Impossible de vérifier la disponibilité d'OR-Tools.")
        return routes
    
    # Créer un dictionnaire des commandes par ID
    orders_by_id = {order.id: order for order in orders}
    
    # Créer un dictionnaire des commandes assignées par agent
    agent_orders: Dict[str, List[Order]] = {agent.id: [] for agent in agents}
    
    for order_id, agent_id in assignment.items():
        if agent_id is not None:
            order = orders_by_id.get(order_id)
            if order:
                agent_orders[agent_id].append(order)
    
    # Calculer la tournée pour chaque agent
    for agent in agents:
        assigned_orders = agent_orders.get(agent.id, [])
        if assigned_orders:
            try:
                route, distance, time = compute_route_for_agent(
                    agent, assigned_orders, warehouse, products_by_id
                )
                routes[agent.id] = (route, distance, time)
            except ImportError as e:
                print(f"⚠️  Erreur lors du calcul de la tournée pour {agent.id}: {e}")
                routes[agent.id] = (None, None, None)
        else:
            routes[agent.id] = (None, None, None)
    
    return routes


# =========================
# 6) Évaluation / affichage
# =========================

def print_report(
    warehouse: Warehouse,
    orders: List[Order],
    agents: List[Agent],
    assignment: Dict[str, Optional[str]],
    products_by_id: Optional[Dict[str, Product]] = None,
    use_routing: bool = False,
    use_minizinc: bool = False,
) -> None:
    total = len(orders)
    assigned = sum(1 for order_id, agent_id in assignment.items() if agent_id is not None)
    unassigned = total - assigned

    dist_total_estimated = compute_total_distance(warehouse, orders)
    
    routes = {}
    dist_total_optimized = 0
    
    if use_routing and products_by_id:
        routes = compute_routes_for_all_agents(
            warehouse, orders, agents, assignment, products_by_id, use_routing=True
        )
        dist_total_optimized = sum(
            distance for _, distance, _ in routes.values() if distance is not None
        )
    
    print("══════════════════════════════════════")
    if use_minizinc:
        print("JOUR 2 — Allocation optimale avec MiniZinc")
    elif use_routing:
        print("JOUR 3 — Allocation avec Optimisation TSP")
    else:
        print("JOUR 1 — Allocation naïve (First-Fit)")
    print("══════════════════════════════════════")
    print(f"Commandes totales : {total}")
    print(f"Commandes assignées: {assigned}")
    print(f"Commandes non assignées: {unassigned}")
    
    if use_routing:
        print(f"\n📊 COMPARAISON DISTANCES:")
        print(f"  Distance estimée (proxy): {dist_total_estimated} unités")
        if dist_total_optimized > 0:
            reduction = ((dist_total_estimated - dist_total_optimized) / dist_total_estimated * 100) if dist_total_estimated > 0 else 0
            print(f"  Distance optimisée (TSP): {dist_total_optimized} unités")
            print(f"  Réduction: {reduction:.1f}%")
        else:
            print(f"  Distance optimisée (TSP): Non calculée")
    else:
        print(f"Distance totale estimée (proxy): {dist_total_estimated}")
    print()

    print("Détail par agent:")
    for agent in agents:
        util_w = 0.0 if agent.capacity_weight == 0 else (agent.used_weight / agent.capacity_weight) * 100
        util_v = 0.0 if agent.capacity_volume == 0 else (agent.used_volume / agent.capacity_volume) * 100
        print(f"- {agent.id} ({agent.type})")
        print(f"  commandes: {len(agent.assigned_orders)} -> {agent.assigned_orders}")
        print(f"  poids: {agent.used_weight:.2f}/{agent.capacity_weight:.2f} kg ({util_w:.1f}%)")
        print(f"  volume: {agent.used_volume:.2f}/{agent.capacity_volume:.2f} dm³ ({util_v:.1f}%)")
        print(f"  vitesse: {agent.speed} m/s")
        if use_routing and agent.id in routes:
            route, distance, time = routes[agent.id]
            if route and distance is not None and time is not None:
                print(f"  🗺️  Tournée TSP:")
                print(f"     Distance: {distance} unités")
                print(f"     Temps: {time:.1f}s ({time/60:.1f} min)")
                print(f"     Ordre: {len(route)} emplacements")
                
                # Vérifier les deadlines
                assigned_orders = [o for o in orders if o.id in agent.assigned_orders]
                all_respected, late_orders = check_deadlines(agent, assigned_orders, time)
                if all_respected:
                    print(f"     ✅ Toutes les deadlines respectées")
                else:
                    print(f"     ⚠️  Commandes en retard: {late_orders}")
        print()

    if unassigned > 0:
        print("Commandes non assignées:")
        for order_id, agent_id in assignment.items():
            if agent_id is None:
                print(f"- {order_id}")
        print()


# =========================
# 7) Main
# =========================

def main(
    warehouse_path: str = "data/warehouse.json",
    products_path: str = "data/products.json",
    agents_path: str = "data/agents.json",
    orders_path: str = "data/orders.json",
    use_routing: bool = False,
    use_minizinc: bool = False,
    solver_name: str = "cbc",
) -> None:
    wh_data = load_json(Path(warehouse_path))
    pr_data = load_json(Path(products_path))
    ag_data = load_json(Path(agents_path))
    or_data = load_json(Path(orders_path))

    warehouse = parse_warehouse(wh_data)
    products_by_id = parse_products(pr_data)
    agents = parse_agents(ag_data)
    orders = parse_orders(or_data)#Les commandes sont triées par heure de réception 

    enrich_orders(orders, products_by_id)

    #Utilisation dans la fonction main First-Fit
    orders_sorted = sort_orders_by_received_time(orders)
    
    # Choisir la méthode d'allocation
    if use_minizinc and MINIZINC_AVAILABLE:
        print("🔧 Utilisation de MiniZinc pour l'allocation optimale...")
        assignment = allocate_with_minizinc(
            orders_sorted, agents, products_by_id, warehouse, solver_name
        )
        # Appliquer l'assignment aux agents pour que le détail (poids, volume, commandes) soit correct
        apply_assignment(assignment, orders_sorted, agents)
    else:
        if use_minizinc and not MINIZINC_AVAILABLE:
            print("⚠️  MiniZinc non disponible, utilisation de l'algorithme glouton")
        assignment = allocate_first_fit(orders_sorted, agents)

    print_report(warehouse, orders_sorted, agents, assignment, products_by_id, use_routing, use_minizinc)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OptiPick - Optimisation de Tournées d'Entrepôt")
    parser.add_argument("--routing", action="store_true", help="Activer l'optimisation TSP (Jour 3)")
    parser.add_argument("--minizinc", action="store_true", help="Utiliser MiniZinc pour l'allocation optimale (Jour 2)")
    parser.add_argument("--solver", default="cbc", help="Solveur MiniZinc à utiliser (cbc, coin-bc, highs, gecode)")
    parser.add_argument("--test", action="store_true", help="Utiliser les fichiers de test (5 commandes, 1 agent)")
    parser.add_argument("--test2", action="store_true", help="Utiliser le 2e jeu de test (10 commandes, 3 robots)")
    parser.add_argument("--test3", action="store_true", help="Utiliser le 3e jeu de test (10 commandes, 3 agents différents: R1, H1, C1)")
    parser.add_argument("--day4", action="store_true", help="Jour 4 : comparaison stratégies (First-Fit, MiniZinc, CP-SAT, Batching+CP-SAT)")
    parser.add_argument("--day5", action="store_true", help="Jour 5 : optimisation stockage, simulation avant/après, dashboard")
    parser.add_argument("--day6", action="store_true", help="Jour 6 : lancer l'interface web (Flask)")
    parser.add_argument("--warehouse", default="data/warehouse.json", help="Chemin vers warehouse.json")
    parser.add_argument("--products", default="data/products.json", help="Chemin vers products.json")
    parser.add_argument("--agents", default="data/agents.json", help="Chemin vers agents.json")
    parser.add_argument("--orders", default="data/orders.json", help="Chemin vers orders.json")
    
    args = parser.parse_args()
    
    # Si --test, --test2 ou --test3 est activé, utiliser les fichiers de test
    if args.test3:
        agents_path = "data/test_agents_3diff.json"
        orders_path = "data/test_orders_10.json"
    elif args.test2:
        agents_path = "data/test_agents_3.json"
        orders_path = "data/test_orders_10.json"
    elif args.test:
        agents_path = "data/test_agents.json"
        orders_path = "data/test_orders.json"
    else:
        agents_path = args.agents
        orders_path = args.orders

    if args.day6:
        import os
        from app import app
        port = int(os.environ.get("FLASK_PORT", 5001))
        print(f"🌐 Interface web OptiPick — http://127.0.0.1:{port}")
        app.run(debug=True, host="0.0.0.0", port=port)
    elif args.day4:
        from src.day4_comparison import run_comparison
        import json
        wh_data = load_json(Path(args.warehouse))
        pr_data = load_json(Path(args.products))
        ag_data = load_json(Path(agents_path))
        or_data = load_json(Path(orders_path))
        warehouse = parse_warehouse(wh_data)
        products_by_id = parse_products(pr_data)
        agents = parse_agents(ag_data)
        orders = parse_orders(or_data)
        enrich_orders(orders, products_by_id)
        print("🔧 Jour 4 — Comparaison des stratégies d'allocation...")
        results = run_comparison(warehouse, orders, agents, products_by_id,
                                 use_minizinc=args.minizinc or MINIZINC_AVAILABLE,
                                 use_cpsat=True, use_batching=True,
                                 solver_name=args.solver)
        print("\n══════════════════════════════════════")
        print("JOUR 4 — Comparaison quantitative")
        print("══════════════════════════════════════\n")
        metrics_only = {}
        for name, data in results.items():
            if "error" in data:
                print(f"  {name}: ❌ {data['error']}")
                continue
            metrics_only[name] = {key: value for key, value in data.items() if key != "assignment"}
            print(f"  {name}:")
            print(f"    Commandes assignées: {data.get('n_assigned', '?')} / {data.get('n_orders', '?')}")
            print(f"    Distance (proxy): {data.get('distance_proxy', '?')} unités")
            print(f"    Temps estimé: {data.get('time_min', 0):.1f} min")
            print(f"    Coût estimé: {data.get('cost_euros', 0):.2f} €")
            if data.get("n_batches"):
                print(f"    Lots créés: {data['n_batches']}")
            print()
        Path("results").mkdir(exist_ok=True)
        with open("results/day4_metrics.json", "w", encoding="utf-8") as metrics_file:
            json.dump(metrics_only, metrics_file, indent=2, ensure_ascii=False)
        print("📁 Métriques enregistrées dans results/day4_metrics.json")
    elif args.day5:
        import json
        from main import allocate_first_fit
        from src.day5_patterns import run_pattern_analysis
        from src.day5_storage import compute_optimized_placement, build_optimized_products
        from src.day5_simulation import run_before_after
        from src.day5_human_robot import recommend
        wh_data = load_json(Path(args.warehouse))
        pr_data = load_json(Path(args.products))
        ag_data = load_json(Path(agents_path))
        or_data = load_json(Path(orders_path))
        warehouse = parse_warehouse(wh_data)
        products_by_id = parse_products(pr_data)
        agents = parse_agents(ag_data)
        orders = parse_orders(or_data)
        enrich_orders(orders, products_by_id)
        orders_sorted = sort_orders_by_received_time(orders)

        print("🔧 Jour 5 — Optimisation du stockage et analyse avancée\n")
        Path("results").mkdir(exist_ok=True)

        # Clones pour simulation (run_before_after mute les agents) et pour allocation finale
        agents_sim = parse_agents([{"id": a.id, "type": a.type, "capacity_weight": a.capacity_weight,
                                   "capacity_volume": a.capacity_volume, "speed": a.speed,
                                   "cost_per_hour": a.cost_per_hour, "restrictions": getattr(a, "restrictions", {})}
                                  for a in agents])
        agents_alloc = parse_agents([{"id": a.id, "type": a.type, "capacity_weight": a.capacity_weight,
                                     "capacity_volume": a.capacity_volume, "speed": a.speed,
                                     "cost_per_hour": a.cost_per_hour, "restrictions": getattr(a, "restrictions", {})}
                                    for a in agents])

        # 5.1 Patterns
        patterns = run_pattern_analysis(orders_sorted, products_by_id, warehouse, top_n=15)
        print("5.1 — Analyse des patterns")
        print("  Top produits (fréquence):", patterns["top_products"][:5])
        print("  Zones visitées:", patterns["zone_visits"])
        with open("results/day5_patterns.json", "w", encoding="utf-8") as f:
            json.dump({
                "top_products": patterns["top_products"],
                "top_co_ordered_pairs": patterns["top_co_ordered_pairs"],
                "zone_visits": patterns["zone_visits"],
                "n_orders": patterns["n_orders"],
            }, f, indent=2, ensure_ascii=False)
        print("  📁 results/day5_patterns.json\n")

        # 5.2 + 5.3 Réorganisation et simulation
        out = run_before_after(warehouse, orders_sorted, agents_sim, products_by_id, n_test_orders=50, seed=42)
        placement = out["placement"]
        metrics = out["metrics"]
        print("5.2–5.3 — Réorganisation et simulation (50 commandes test)")
        print("  Distance actuelle:", metrics["distance_current"], "| optimisée:", metrics["distance_optimized"])
        print("  Réduction:", metrics["reduction_percent"], "%")
        placement_serializable = {pid: [loc.x, loc.y] for pid, loc in placement.items()}
        with open("results/day5_placement.json", "w", encoding="utf-8") as f:
            json.dump(placement_serializable, f, indent=2)
        with open("results/day5_simulation.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print("  📁 results/day5_placement.json, results/day5_simulation.json\n")

        # 5.4 Humain–robot
        assign = allocate_first_fit(orders_sorted, agents_alloc)
        rec = recommend(assign, orders_sorted, agents_alloc)
        print("5.4 — Coopération humain–robot")
        for t, s in rec["stats_by_type"].items():
            print(f"  {t}: {s['n_orders']} commandes ({s['share_percent']}%)")
        for r in rec["recommendations"]:
            print("  →", r)
        with open("results/day5_human_robot.json", "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2, ensure_ascii=False)
        print("  📁 results/day5_human_robot.json\n")

        # 5.5 Dashboard
        zone_visits = patterns["zone_visits"]
        try:
            from src.day5_dashboard import run_dashboard
            ok = run_dashboard(warehouse, products_by_id, orders_sorted, agents_alloc, assign, zone_visits,
                               output_path=Path("results/day5_dashboard.png"), use_routing=args.routing)
            if ok:
                print("5.5 — Dashboard enregistré : results/day5_dashboard.png")
            else:
                print("5.5 — Dashboard non généré (pip install matplotlib)")
        except Exception as e:
            print("5.5 — Dashboard non généré:", e)
    else:
        main(
            warehouse_path=args.warehouse,
            products_path=args.products,
            agents_path=agents_path,
            orders_path=orders_path,
            use_routing=args.routing,
            use_minizinc=args.minizinc,
            solver_name=args.solver,
        )