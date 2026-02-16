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
from src.constraints import (
    can_agent_take_order_with_constraints,
)
try:
    from src.minizinc_solver import (
        allocate_with_minizinc,
        check_minizinc_available,
    )
    MINIZINC_AVAILABLE = True
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

        for it in order.items:
            p = products_by_id.get(it.product_id)
            if p is None:
                raise KeyError(f"Produit introuvable: {it.product_id} (dans {order.id})")

            total_w += p.weight * it.quantity
            total_v += p.volume * it.quantity

            key = (p.location.x, p.location.y)
            if key not in seen:
                seen.add(key)
                locs.append(p.location)

        order.total_weight = total_w
        order.total_volume = total_v
        order.unique_locations = locs


# =========================
# 3) Allocation avec contraintes (Jour 2)
# =========================


# Tri des commandes par ordre d'arrivée
def sort_orders_by_received_time(orders: List[Order]) -> List[Order]:
    # "HH:MM" -> minutes
    def to_minutes(hhmm: str) -> int:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    return sorted(orders, key=lambda o: to_minutes(o.received_time))
#Convertit l'heure de réception en minutes
#Trie les commandes par ordre chronologique


def sort_agents_by_priority(agents: List[Agent]) -> List[Agent]:
    """
    Trie les agents par priorité : robots d'abord, puis humains, puis chariots.
    (Jour 2 : stratégie gloutonne améliorée)
    """
    def priority(agent: Agent) -> int:
        if agent.type == "robot":
            return 0
        elif agent.type == "human":
            return 1
        elif agent.type == "cart":
            return 2
        return 3
    
    return sorted(agents, key=priority)


#Fonction d'allocation First-Fit avec contraintes (Jour 2)
def allocate_first_fit(
    orders: List[Order],
    agents: List[Agent],
    products_by_id: Dict[str, Product],
    warehouse: Warehouse
) -> Dict[str, Optional[str]]:
    """
    JOUR 2 : Allocation avec toutes les contraintes dures.
    Algorithme glouton amélioré :
    - Pour chaque commande (par ordre d'arrivée)
    - Tester chaque agent dans l'ordre (robots d'abord)
    - Vérifier toutes les contraintes
    - Assigner au premier agent valide
    
    Retourne: {order_id: agent_id or None}
    """
    assignment: Dict[str, Optional[str]] = {}
    agents_sorted = sort_agents_by_priority(agents)  # Robots en premier

    for order in orders:  # ← Pour chaque commande (par ordre d'arrivée)
        assigned = False
        for agent in agents_sorted:  # ← Parcourt les agents (robots d'abord)
            # Vérifier toutes les contraintes (Jour 2)
            if can_agent_take_order_with_constraints(
                agent=agent,
                order=order,
                products_by_id=products_by_id,
                warehouse=warehouse,
                restrictions=agent.restrictions,
                agents=agents,
                assignment=assignment
            ):
                agent.assign(order)
                assignment[order.id] = agent.id
                assigned = True
                break  # ← S'arrête au premier agent valide
        if not assigned:
            assignment[order.id] = None  # ← Aucun agent disponible respectant les contraintes

    return assignment


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
    return sum(estimate_order_distance(warehouse, o) for o in orders)


# =========================
# 5) Évaluation / affichage
# =========================

def print_report(warehouse: Warehouse, orders: List[Order], agents: List[Agent], assignment: Dict[str, Optional[str]], use_minizinc: bool = False) -> None:
    total = len(orders)
    assigned = sum(1 for oid, aid in assignment.items() if aid is not None)
    unassigned = total - assigned

    dist_total = compute_total_distance(warehouse, orders)

    print("══════════════════════════════════════")
    if use_minizinc:
        print("JOUR 2 — Allocation optimale avec MiniZinc")
    else:
        print("JOUR 2 — Allocation avec contraintes (glouton)")
    print("══════════════════════════════════════")
    print(f"Commandes totales : {total}")
    print(f"Commandes assignées: {assigned}")
    print(f"Commandes non assignées: {unassigned}")
    print(f"Distance totale estimée (proxy): {dist_total}")
    print()

    print("Détail par agent:")
    for a in agents:
        util_w = 0.0 if a.capacity_weight == 0 else (a.used_weight / a.capacity_weight) * 100
        util_v = 0.0 if a.capacity_volume == 0 else (a.used_volume / a.capacity_volume) * 100
        print(f"- {a.id} ({a.type})")
        print(f"  commandes: {len(a.assigned_orders)} -> {a.assigned_orders}")
        print(f"  poids: {a.used_weight:.2f}/{a.capacity_weight:.2f} kg ({util_w:.1f}%)")
        print(f"  volume: {a.used_volume:.2f}/{a.capacity_volume:.2f} dm³ ({util_v:.1f}%)")
    print()

    if unassigned > 0:
        print("Commandes non assignées (contraintes non respectées):")
        for oid, aid in assignment.items():
            if aid is None:
                print(f"- {oid}")
        print()


# =========================
# 6) Main
# =========================

def main(
    warehouse_path: str = "data/warehouse.json",
    products_path: str = "data/products.json",
    agents_path: str = "data/agents.json",
    orders_path: str = "data/orders.json",
    use_minizinc: bool = False,
    solver_name: str = "gecode",
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

    #Utilisation dans la fonction main avec contraintes (Jour 2)
    orders_sorted = sort_orders_by_received_time(orders)
    
    # Choisir entre algorithme glouton et MiniZinc
    if use_minizinc and MINIZINC_AVAILABLE:
        print("🔧 Utilisation de MiniZinc pour l'allocation optimale...")
        try:
            assignment = allocate_with_minizinc(
                orders_sorted,
                agents,
                products_by_id,
                warehouse,
                solver_name=solver_name
            )
            print("✅ Résolution MiniZinc terminée\n")
        except Exception as e:
            print(f"⚠️  Erreur MiniZinc: {e}")
            print("🔄 Basculement vers l'algorithme glouton...\n")
            assignment = allocate_first_fit(
                orders_sorted,
                agents,
                products_by_id,
                warehouse
            )
    else:
        if use_minizinc:
            print("⚠️  MiniZinc n'est pas disponible. Utilisation de l'algorithme glouton.\n")
        assignment = allocate_first_fit(
            orders_sorted,
            agents,
            products_by_id,
            warehouse
        )

    print_report(warehouse, orders_sorted, agents, assignment, use_minizinc=use_minizinc and MINIZINC_AVAILABLE)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OptiPick - Allocation optimale des commandes")
    parser.add_argument(
        "--minizinc",
        action="store_true",
        help="Utiliser MiniZinc pour l'allocation optimale (au lieu de l'algorithme glouton)"
    )
    parser.add_argument(
        "--solver",
        type=str,
        default="gecode",
        help="Solveur MiniZinc à utiliser (gecode, chuffed, etc.)"
    )
    args = parser.parse_args()
    
    main(use_minizinc=args.minizinc, solver_name=args.solver)