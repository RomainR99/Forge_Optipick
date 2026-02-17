"""
Jour 5.4 : Analyse coopération humain-robot.
- % commandes traitées par robots vs humains (et chariots)
- Types de commandes mieux adaptées à chaque type d'agent
- Recommandations (plus de robots ?, quoi automatiser ?, formation humains)
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Any, Optional

from src.models import Order, Agent


def agent_type_stats(
    assignment: Dict[str, Optional[str]],
    agents: List[Agent],
) -> Dict[str, Dict[str, Any]]:
    """
    Pour chaque type d'agent (robot, human, cart), retourne :
    - n_orders : nombre de commandes assignées
    - agent_ids : liste des ids
    - share_percent : part en %
    """
    orders_by_agent: Dict[str, str] = {}  # order_id -> agent_id
    for order_id, agent_id in assignment.items():
        if agent_id:
            orders_by_agent[order_id] = agent_id

    type_to_agents: Dict[str, List[Agent]] = defaultdict(list)
    for agent in agents:
        type_to_agents[agent.type].append(agent)

    total_assigned = len(orders_by_agent)
    result: Dict[str, Dict[str, Any]] = {}

    for agent_type, type_agents in type_to_agents.items():
        agent_ids = [a.id for a in type_agents]
        n_orders = sum(
            1 for aid in assignment.values()
            if aid in agent_ids
        )
        share = (n_orders / total_assigned * 100) if total_assigned else 0.0
        result[agent_type] = {
            "n_orders": n_orders,
            "agent_ids": agent_ids,
            "share_percent": round(share, 1),
        }
    result["_total_assigned"] = total_assigned
    result["_total_orders"] = len(assignment)
    return result


def order_profile(order: Order) -> Dict[str, Any]:
    """Profil d'une commande : nb items, poids/volume si disponibles."""
    n_items = sum(item.quantity for item in order.items)
    return {
        "n_items": n_items,
        "n_products": len(order.items),
        "weight": getattr(order, "total_weight", 0),
        "volume": getattr(order, "total_volume", 0),
    }


def orders_by_agent_type(
    assignment: Dict[str, Optional[str]],
    orders: List[Order],
    agents: List[Agent],
) -> Dict[str, List[Order]]:
    """Retourne les commandes assignées à chaque type d'agent."""
    type_to_ids: Dict[str, set] = defaultdict(set)
    for agent in agents:
        type_to_ids[agent.type].add(agent.id)
    orders_by_id = {o.id: o for o in orders}
    result: Dict[str, List[Order]] = defaultdict(list)
    for order_id, agent_id in assignment.items():
        if not agent_id:
            continue
        order = orders_by_id.get(order_id)
        if not order:
            continue
        for atype, ids in type_to_ids.items():
            if agent_id in ids:
                result[atype].append(order)
                break
    return dict(result)


def recommend(
    assignment: Dict[str, Optional[str]],
    orders: List[Order],
    agents: List[Agent],
) -> Dict[str, Any]:
    """
    Analyse et recommandations :
    - part robots / humains / chariots
    - types de commandes par agent (léger/lourd, express/standard)
    - recommandations texte
    """
    stats = agent_type_stats(assignment, agents)
    by_type = orders_by_agent_type(assignment, orders, agents)
    total = stats.get("_total_orders", 0)
    assigned = stats.get("_total_assigned", 0)

    # Profils moyens par type
    profiles: Dict[str, Dict[str, float]] = {}
    for atype, order_list in by_type.items():
        if not order_list:
            profiles[atype] = {"n_items_avg": 0, "weight_avg": 0}
            continue
        n_items = [order_profile(o)["n_items"] for o in order_list]
        weights = [order_profile(o)["weight"] for o in order_list]
        profiles[atype] = {
            "n_items_avg": sum(n_items) / len(n_items),
            "weight_avg": sum(weights) / len(weights) if weights else 0,
        }

    recommendations = []
    robot_share = stats.get("robot", {}).get("share_percent", 0)
    human_share = stats.get("human", {}).get("share_percent", 0)
    cart_share = stats.get("cart", {}).get("share_percent", 0)

    if robot_share > 60:
        recommendations.append(
            "Les robots traitent déjà une large part des commandes. "
            "Vérifier la capacité des robots avant d’en ajouter."
        )
    elif robot_share < 30 and total > 20:
        recommendations.append(
            "Envisager d’augmenter le nombre de robots pour les commandes légères et standard, "
            "afin de réduire le coût horaire et libérer les humains pour les tâches à forte valeur."
        )
    else:
        recommendations.append(
            "Répartition actuelle équilibrée. Analyser les pics de charge pour ajuster la flotte."
        )

    recommendations.append(
        "Automatiser en priorité les commandes à peu de lignes, poids modéré et priorité standard, "
        "où les robots sont les plus efficaces."
    )
    recommendations.append(
        "Former les humains aux commandes express, fragiles ou à forte valeur, "
        "et à la supervision des robots."
    )

    return {
        "stats_by_type": {k: v for k, v in stats.items() if not k.startswith("_")},
        "total_orders": total,
        "total_assigned": assigned,
        "profiles_by_type": profiles,
        "recommendations": recommendations,
    }
