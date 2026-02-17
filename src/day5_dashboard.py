"""
Jour 5.5 : Dashboard de monitoring.
- Carte de l'entrepôt avec emplacements et zones
- Tournées des agents (trajets)
- Statistiques
- Heatmap des zones visitées
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.colors as mcolors
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

from src.models import Warehouse, Product, Order, Agent, Location


def _draw_warehouse_zones(ax, warehouse: Warehouse) -> None:
    """Dessine les zones de l'entrepôt (rectangles ou points)."""
    colors_zone = {"A": "#3498db", "B": "#2ecc71", "C": "#e74c3c", "D": "#9b59b6", "E": "#f39c12"}
    for zone_name, locs in warehouse.zones.items():
        if not locs:
            continue
        color = colors_zone.get(zone_name, "#95a5a6")
        xs = [loc.x for loc in locs]
        ys = [loc.y for loc in locs]
        ax.scatter(xs, ys, c=color, s=80, label=f"Zone {zone_name}", zorder=2, edgecolors="black", linewidths=0.5)
    ax.scatter(
        [warehouse.entry_point.x], [warehouse.entry_point.y],
        c="black", s=200, marker="*", label="Entrée", zorder=5
    )


def _draw_product_locations(ax, products_by_id: Dict[str, Product], alpha: float = 0.6) -> None:
    """Dessine tous les emplacements produits (points gris)."""
    xs = [p.location.x for p in products_by_id.values()]
    ys = [p.location.y for p in products_by_id.values()]
    ax.scatter(xs, ys, c="gray", s=15, alpha=alpha, zorder=1)


def _draw_routes(
    ax,
    routes: Dict[str, Tuple[Optional[List[Location]], Optional[int], Optional[float]]],
    entry: Location,
    colors: Optional[Dict[str, str]] = None,
) -> None:
    """Dessine les tournées des agents (lignes)."""
    if not routes or not colors:
        return
    default_colors = ["#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#f39c12"]
    for i, (agent_id, (route_locs, _, _)) in enumerate(routes.items()):
        if not route_locs:
            continue
        color = (colors or {}).get(agent_id) or default_colors[i % len(default_colors)]
        xs = [loc.x for loc in route_locs]
        ys = [loc.y for loc in route_locs]
        ax.plot(xs, ys, color=color, linewidth=1.5, alpha=0.8, zorder=3)
        ax.scatter(xs, ys, c=color, s=30, zorder=4)


def _heatmap_zones(
    ax,
    warehouse: Warehouse,
    zone_visits: Dict[str, int],
) -> None:
    """Heatmap : une barre par zone avec intensité = nombre de visites."""
    zones = list(warehouse.zones.keys())
    values = [zone_visits.get(z, 0) for z in zones]
    colors = ["#3498db", "#2ecc71", "#e74c3c", "#9b59b6", "#f39c12"][: len(zones)]
    bars = ax.bar(zones, values, color=colors)
    ax.set_ylabel("Nombre de visites (commandes)")
    ax.set_title("Zones les plus visitées")
    for bar, v in zip(bars, values):
        if v > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, str(v), ha="center", fontsize=10)


def build_dashboard(
    warehouse: Warehouse,
    products_by_id: Dict[str, Product],
    orders: List[Order],
    agents: List[Agent],
    assignment: Dict[str, Optional[str]],
    zone_visits: Dict[str, int],
    routes: Optional[Dict[str, Tuple[Optional[List[Location]], Optional[int], Optional[float]]]] = None,
    stats_text: Optional[str] = None,
    output_path: Optional[Path] = None,
) -> bool:
    """
    Génère le dashboard (carte + heatmap + stats).
    Retourne True si succès.
    """
    if not HAS_MPL:
        return False

    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.2, 1], height_ratios=[1, 1])

    # 1) Carte entrepôt + emplacements + tournées
    ax_map = fig.add_subplot(gs[0, 0])
    ax_map.set_xlim(-0.5, warehouse.width)
    ax_map.set_ylim(-0.5, warehouse.height)
    ax_map.set_aspect("equal")
    ax_map.invert_yaxis()
    _draw_warehouse_zones(ax_map, warehouse)
    _draw_product_locations(ax_map, products_by_id)
    if routes:
        _draw_routes(ax_map, routes, warehouse.entry_point)
    ax_map.set_xlabel("x")
    ax_map.set_ylabel("y")
    ax_map.set_title("Entrepôt — Zones, emplacements et tournées")
    ax_map.legend(loc="upper left", fontsize=7)
    ax_map.grid(True, alpha=0.3)

    # 2) Heatmap zones
    ax_heat = fig.add_subplot(gs[0, 1])
    _heatmap_zones(ax_heat, warehouse, zone_visits)

    # 3) Stats texte
    ax_stats = fig.add_subplot(gs[1, :])
    ax_stats.axis("off")
    n_orders = len(orders)
    n_assigned = sum(1 for a in assignment.values() if a is not None)
    default_stats = (
        f"Commandes : {n_orders} total, {n_assigned} assignées\n"
        f"Agents : {len(agents)}"
    )
    ax_stats.text(0.1, 0.5, stats_text or default_stats, fontsize=11, verticalalignment="center", family="monospace")

    plt.tight_layout()
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=120, bbox_inches="tight")
        plt.close()
        return True
    plt.close()
    return True


def run_dashboard(
    warehouse: Warehouse,
    products_by_id: Dict[str, Product],
    orders: List[Order],
    agents: List[Agent],
    assignment: Dict[str, Optional[str]],
    zone_visits: Dict[str, int],
    output_path: Optional[Path] = None,
    use_routing: bool = False,
) -> bool:
    """
    Construit les routes si use_routing=True puis appelle build_dashboard.
    """
    routes = None
    if use_routing:
        try:
            from main import compute_routes_for_all_agents
            routes = compute_routes_for_all_agents(
                warehouse, orders, agents, assignment, products_by_id, use_routing=True
            )
        except Exception:
            pass
    return build_dashboard(
        warehouse,
        products_by_id,
        orders,
        agents,
        assignment,
        zone_visits,
        routes=routes,
        output_path=output_path,
    )
