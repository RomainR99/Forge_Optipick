import json
from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from src.loader import load_data
from src.utils import manhattan, build_zone_map  # ✅ on utilise build_zone_map pour colorer TOUS les carreaux

RESULTS_DIR = Path("results")

st.set_page_config(page_title="OptiPick — Dashboard", layout="wide")

# Pastels clairs (zones)
ZONE_COLORS = {
    "A": "#CFE6FF",  # bleu très clair
    "B": "#FFE9C7",  # jaune/orange très clair
    "C": "#FFD3D3",  # rose très clair
    "D": "#D9F5D9",  # vert très clair
    "E": "#D6F4F2",  # turquoise très clair
}


def nearest_neighbor_route(entry, points):
    """Heuristique simple : plus proche voisin."""
    if not points:
        return [entry, entry]

    remaining = points.copy()
    route = [entry]
    current = entry

    while remaining:
        nxt = min(remaining, key=lambda p: manhattan(current, p))
        route.append(nxt)
        current = nxt
        remaining.remove(nxt)

    route.append(entry)
    return route


# ---------------------------------------------------------
# Fond "grille" colorée : colorer TOUS les carreaux de zone
# ---------------------------------------------------------
def draw_zone_grid_background(ax, warehouse, alpha=0.45):
    """
    Dessine des carreaux colorés en arrière-plan pour TOUS les carreaux de zone.
    On s'appuie sur build_zone_map(warehouse) qui retourne (x,y)->"A/B/C/D/E" pour chaque case.
    """
    zone_map = build_zone_map(warehouse)  # ✅ clé du fix : inclut toutes les cases "lettres"
    if not zone_map:
        return 0, 0

    max_x = max(x for (x, _) in zone_map.keys())
    max_y = max(y for (_, y) in zone_map.keys())

    # Dessiner chaque case présente dans zone_map
    for (x, y), zone in zone_map.items():
        if zone is None:
            continue
        zone = str(zone).strip().upper()
        color = ZONE_COLORS.get(zone, "#DDDDDD")

        rect = patches.Rectangle(
            (x, y), 1, 1,
            linewidth=0.8,
            edgecolor="white",
            facecolor=color,
            alpha=alpha
        )
        ax.add_patch(rect)

    return max_x, max_y


# -----------------------------
# Graphiques
# -----------------------------
def plot_warehouse(warehouse):
    """
    Plan minimal (comme au début) :
    - arrière plan = tous les carreaux de zone colorés pastel
    - pas de lettres
    - étoile noire à l'entrée
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    max_x, max_y = draw_zone_grid_background(ax, warehouse, alpha=0.50)

    # Entrée ⭐ (comme au début)
    ex, ey = warehouse["entry_point"]
    ax.scatter([ex + 0.5], [ey + 0.5], s=380, marker="*", color="black", label="Entrée", zorder=5)

    ax.set_title("Plan de l'entrepôt (zones + entrée)")
    ax.set_xlabel("x")
    ax.set_ylabel("y")

    # Axes calibrés sur toute la grille
    ax.set_xlim(0, max_x + 1)
    ax.set_ylim(0, max_y + 1)
    ax.set_aspect("equal")
    ax.invert_yaxis()

    ax.set_xticks(range(0, max_x + 2))
    ax.set_yticks(range(0, max_y + 2))
    ax.grid(True, alpha=0.18)

    # Légende zones
    handles = [patches.Patch(color=ZONE_COLORS[z], label=f"Zone {z}") for z in ["A", "B", "C", "D", "E"]]
    ax.legend(handles=handles + ax.get_legend_handles_labels()[0], loc="lower right")

    return fig


def plot_agent_points_and_route(warehouse, allocation, orders_map, product_map, agent_id):
    """
    Graph circuit : NE CHANGE PAS la logique du circuit.
    On met juste le même fond coloré en arrière-plan.
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    max_x, max_y = draw_zone_grid_background(ax, warehouse, alpha=0.30)

    entry = tuple(warehouse["entry_point"])
    ax.scatter([entry[0] + 0.5], [entry[1] + 0.5], s=380, marker="*", color="black", label="Entrée", zorder=6)

    # Stops produits
    pts = []
    for oid in allocation.get(agent_id, []):
        order = orders_map[oid]
        for item in order["items"]:
            p = product_map[item["product_id"]]
            pts.append(tuple(p["location"]))

    pts_unique = list(dict.fromkeys(pts))

    if pts_unique:
        xs = [p[0] + 0.5 for p in pts_unique]
        ys = [p[1] + 0.5 for p in pts_unique]
        ax.scatter(xs, ys, s=120, color="#333333", alpha=0.85, label="Stops (produits)", zorder=7)

        # Circuit (inchangé)
        route = nearest_neighbor_route(entry, pts_unique)
        rx = [p[0] + 0.5 for p in route]
        ry = [p[1] + 0.5 for p in route]
        ax.plot(rx, ry, linewidth=2.2, color="black", alpha=0.8, label="Circuit (nearest neighbor)", zorder=8)

    ax.set_title(f"Produits à ramasser + circuit — {agent_id}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")

    ax.set_xlim(0, max_x + 1)
    ax.set_ylim(0, max_y + 1)
    ax.set_aspect("equal")
    ax.invert_yaxis()

    ax.set_xticks(range(0, max_x + 2))
    ax.set_yticks(range(0, max_y + 2))
    ax.grid(True, alpha=0.18)

    ax.legend(loc="lower right")
    return fig


def plot_bar(df, x_col, y_col, title):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(df[x_col], df[y_col])
    ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.grid(True, axis="y", alpha=0.3)
    return fig


# -----------------------------
# Charger résultats
# -----------------------------
alloc_file = RESULTS_DIR / "allocation.json"
metrics_file = RESULTS_DIR / "metrics.json"
unassigned_file = RESULTS_DIR / "unassigned_orders.json"

st.title("OptiPick — Dashboard (FR)")
st.caption("MiniZinc résout via `python3 main.py` puis Streamlit affiche les résultats.")

if not alloc_file.exists() or not metrics_file.exists():
    st.error("Aucun résultat trouvé. Lance d'abord :  python3 main.py")
    st.stop()

allocation = json.loads(alloc_file.read_text(encoding="utf-8"))
metrics = json.loads(metrics_file.read_text(encoding="utf-8"))

# Charger data
orders, agents, products, warehouse = load_data()
orders_map = {o["id"]: o for o in orders}
product_map = {p["id"]: p for p in products}
agents_map = {a["id"]: a for a in agents}

agent_ids = list(allocation.keys())
all_order_ids = sorted(list(orders_map.keys()))

# map commande -> agent
order_to_agent = {}
for aid, oids in allocation.items():
    for oid in oids:
        order_to_agent[oid] = aid


# -----------------------------
# Sidebar : 2 listes déroulantes (agent + commande)
# -----------------------------
st.sidebar.title("🔎 Sélection")

agent_selected = st.sidebar.selectbox("Choisir un agent", agent_ids, index=0)

order_selected = st.sidebar.selectbox(
    "Choisir une commande",
    ["(aucune)"] + all_order_ids,
    index=0
)

st.sidebar.markdown("---")
st.sidebar.code("1) python3 main.py\n2) python3 -m streamlit run app.py")


# -----------------------------
# Détails commande (si sélectionnée)
# -----------------------------
if order_selected != "(aucune)":
    oid = order_selected
    st.markdown("---")
    st.subheader(f"📦 Détails commande — {oid}")

    assigned_agent = order_to_agent.get(oid)
    if assigned_agent:
        st.success(f"✅ Assignée à : **{assigned_agent}**")
    else:
        st.warning("⚠️ Non assignée (ou filtrée). Vérifie `unassigned_orders.json`.")

    order = orders_map[oid]
    st.write("**Received :**", order.get("received_time"), " | **Deadline :**", order.get("deadline"))

    rows = []
    for it in order["items"]:
        p = product_map[it["product_id"]]
        rows.append({
            "product_id": p["id"],
            "name": p.get("name", ""),
            "qty": it["quantity"],
            "fragile": bool(p.get("fragile", False)),
            "weight_unit": p.get("weight"),
            "volume_unit": p.get("volume"),
            "location": tuple(p.get("location", (None, None))),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


# -----------------------------
# Commandes non assignées (optionnelles)
# -----------------------------
st.markdown("---")
st.subheader("🚫 Commandes non assignées")

if unassigned_file.exists():
    unassigned = json.loads(unassigned_file.read_text(encoding="utf-8"))
    if len(unassigned) == 0:
        st.success("✅ Toutes les commandes ont été assignées.")
    else:
        df_unassigned = pd.DataFrame(unassigned)
        if "order_id" in df_unassigned.columns:
            df_unassigned = df_unassigned.sort_values(by="order_id")

        st.error(f"{len(df_unassigned)} commande(s) non assignée(s).")

        if "reason" in df_unassigned.columns:
            reason_counts = df_unassigned["reason"].value_counts().reset_index()
            reason_counts.columns = ["Raison", "Nombre"]
            st.dataframe(reason_counts, use_container_width=True)

        show_details = st.checkbox("Afficher le détail des commandes non assignées", value=False)
        if show_details:
            mapping = {"C2_incompatible_products": "C2 : produits incompatibles"}
            if "reason" in df_unassigned.columns:
                df_unassigned["reason"] = df_unassigned["reason"].map(lambda r: mapping.get(r, r))
            st.dataframe(df_unassigned, use_container_width=True)
else:
    st.info("Aucun fichier `results/unassigned_orders.json` trouvé (relance `python3 main.py`).")


# -----------------------------
# DataFrames métriques
# -----------------------------
df_metrics = pd.DataFrame(metrics).sort_values(by="orders", ascending=False)
df_metrics["type"] = df_metrics["agent"].map(lambda a: agents_map.get(a, {}).get("type", "?"))

# -----------------------------
# Layout principal
# -----------------------------
st.markdown("---")
colA, colB = st.columns([1, 1])

with colA:
    st.subheader("Métriques par agent")
    st.dataframe(df_metrics, use_container_width=True)

with colB:
    st.subheader("Plan de l'entrepôt (pastel, fond léger)")
    st.pyplot(plot_warehouse(warehouse), clear_figure=True)

st.markdown("---")
st.subheader("Graphiques (résumé)")

c1, c2, c3 = st.columns(3)
with c1:
    st.pyplot(plot_bar(df_metrics, "agent", "orders", "Nombre de commandes par agent"), clear_figure=True)
with c2:
    st.pyplot(plot_bar(df_metrics, "agent", "weight", "Poids total (kg) par agent"), clear_figure=True)
with c3:
    st.pyplot(plot_bar(df_metrics, "agent", "volume", "Volume total (dm3) par agent"), clear_figure=True)

# -----------------------------
# Détails agent + circuit
# -----------------------------
st.markdown("---")
st.subheader(f"Détails — {agent_selected}")

col1, col2 = st.columns([1, 1])

with col1:
    row = df_metrics[df_metrics["agent"] == agent_selected].iloc[0].to_dict()
    st.write("**Type :**", row.get("type"))
    st.write("**Commandes :**", int(row.get("orders", 0)))
    st.write("**Poids total :**", row.get("weight"), "kg")
    st.write("**Volume total :**", row.get("volume"), "dm3")

    st.write("**Liste des commandes :**")
    st.code("\n".join(allocation.get(agent_selected, [])) if allocation.get(agent_selected) else "(aucune)")

    entry = tuple(warehouse["entry_point"])
    pts = []
    for oid in allocation.get(agent_selected, []):
        order = orders_map[oid]
        for item in order["items"]:
            p = product_map[item["product_id"]]
            pts.append(tuple(p["location"]))
    pts_unique = list(dict.fromkeys(pts))
    route = nearest_neighbor_route(entry, pts_unique)

    st.write("**Circuit proposé (nearest neighbor)** :")
    st.code(" -> ".join([str(p) for p in route]))

with col2:
    st.pyplot(
        plot_agent_points_and_route(warehouse, allocation, orders_map, product_map, agent_selected),
        clear_figure=True
    )

