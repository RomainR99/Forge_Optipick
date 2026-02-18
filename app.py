import json
from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from src.loader import load_data
from src.utils import build_zone_map

RESULTS_DIR = Path("results")

st.set_page_config(page_title="OptiPick — Dashboard", layout="wide")


# -----------------------------
# Helpers graphiques
# -----------------------------
def plot_warehouse(warehouse):
    fig, ax = plt.subplots(figsize=(8, 6))

    # zones
    for zone, data in warehouse["zones"].items():
        xs = [c[0] for c in data["coords"]]
        ys = [c[1] for c in data["coords"]]
        ax.scatter(xs, ys, s=380, alpha=0.20, label=f"Zone {zone}")

    # entrée
    entry = warehouse["entry_point"]
    ax.scatter([entry[0]], [entry[1]], s=300, marker="*", label="Entrée")

    ax.set_title("Plan de l'entrepôt (zones + entrée)")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True)
    ax.legend()
    ax.invert_yaxis()
    return fig


def plot_agent_points(warehouse, allocation, orders_map, product_map, agent_id):
    fig, ax = plt.subplots(figsize=(8, 6))

    entry = warehouse["entry_point"]
    ax.scatter([entry[0]], [entry[1]], s=300, marker="*", label="Entrée")

    pts_x, pts_y = [], []
    for oid in allocation.get(agent_id, []):
        order = orders_map[oid]
        for item in order["items"]:
            p = product_map[item["product_id"]]
            x, y = p["location"]
            pts_x.append(x)
            pts_y.append(y)

    if pts_x:
        ax.scatter(pts_x, pts_y, s=90, label=f"Produits ({agent_id})")

    ax.set_title(f"Produits à ramasser — {agent_id}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True)
    ax.legend()
    ax.invert_yaxis()
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
# Charger résultats (générés par main.py)
# -----------------------------
alloc_file = RESULTS_DIR / "allocation.json"
metrics_file = RESULTS_DIR / "metrics.json"

st.title("OptiPick — Dashboard (FR)")
st.caption("Version stable : MiniZinc résout via `python3 main.py` puis Streamlit affiche.")

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

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("Paramètres")
agent_selected = st.sidebar.selectbox("Choisir un agent", agent_ids)

st.sidebar.markdown("---")

# -----------------------------
# DataFrames
# -----------------------------
df_metrics = pd.DataFrame(metrics)
df_metrics = df_metrics.sort_values(by="orders", ascending=False)

# Ajoute type agent si dispo
df_metrics["type"] = df_metrics["agent"].map(lambda a: agents_map.get(a, {}).get("type", "?"))

# -----------------------------
# Layout
# -----------------------------
colA, colB = st.columns([1, 1])

with colA:
    st.subheader("Métriques par agent")
    st.dataframe(df_metrics, use_container_width=True)

with colB:
    st.subheader("Plan de l'entrepôt")
    st.pyplot(plot_warehouse(warehouse), clear_figure=True)

st.markdown("---")

# Graphs principaux
st.subheader("Graphiques (résumé)")

c1, c2, c3 = st.columns(3)

with c1:
    st.pyplot(plot_bar(df_metrics, "agent", "orders", "Nombre de commandes par agent"), clear_figure=True)

with c2:
    st.pyplot(plot_bar(df_metrics, "agent", "weight", "Poids total (kg) par agent"), clear_figure=True)

with c3:
    st.pyplot(plot_bar(df_metrics, "agent", "volume", "Volume total (dm3) par agent"), clear_figure=True)

st.markdown("---")

# Détails agent
st.subheader(f"Détails — {agent_selected}")

col1, col2 = st.columns([1, 1])

with col1:
    # petit résumé texte
    row = df_metrics[df_metrics["agent"] == agent_selected].iloc[0].to_dict()
    st.write("**Type :**", row.get("type"))
    st.write("**Commandes :**", int(row.get("orders", 0)))
    st.write("**Poids total :**", row.get("weight"), "kg")
    st.write("**Volume total :**", row.get("volume"), "dm3")

    st.write("**Liste des commandes :**")
    st.code("\n".join(allocation.get(agent_selected, [])) if allocation.get(agent_selected) else "(aucune)")

with col2:
    st.pyplot(
        plot_agent_points(warehouse, allocation, orders_map, product_map, agent_selected),
        clear_figure=True
    )

