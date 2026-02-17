"""
Jour 4 : Génère les graphiques de performance à partir de results/day4_metrics.json.
Usage : python scripts/plot_day4_metrics.py
"""
import json
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use("Agg")
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

def main():
    metrics_path = Path(__file__).parent.parent / "results" / "day4_metrics.json"
    if not metrics_path.exists():
        print("Fichier results/day4_metrics.json introuvable. Lancez d'abord: python main.py --day4 --test3")
        return
    with open(metrics_path, encoding="utf-8") as metrics_file:
        data = json.load(metrics_file)

    # Exclure les entrées avec erreur
    strategies = [strategy_key for strategy_key, strategy_data in data.items()
                  if isinstance(strategy_data, dict) and "error" not in strategy_data]
    if not strategies:
        print("Aucune métrique valide dans le fichier.")
        return

    if not HAS_MPL:
        print("matplotlib non installé. pip install matplotlib pour générer les graphiques.")
        return

    labels = {"first_fit": "First-Fit (J1)", "minizinc": "MiniZinc (J2)", "cpsat": "CP-SAT (J4)", "batching_cpsat": "Batching+CP-SAT"}
    names = [labels.get(strategy_name, strategy_name) for strategy_name in strategies]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    # Commandes assignées
    ax = axes[0]
    n_assigned = [data[strategy_name].get("n_assigned", 0) for strategy_name in strategies]
    ax.bar(names, n_assigned, color=["#2ecc71", "#3498db", "#9b59b6", "#e74c3c"])
    ax.set_ylabel("Commandes assignées")
    ax.set_title("Nombre de commandes assignées")

    # Distance proxy
    ax = axes[1]
    distances = [data[strategy_name].get("distance_proxy", 0) for strategy_name in strategies]
    ax.bar(names, distances, color=["#2ecc71", "#3498db", "#9b59b6", "#e74c3c"])
    ax.set_ylabel("Distance (proxy)")
    ax.set_title("Distance totale estimée")

    # Coût (€)
    ax = axes[2]
    costs = [data[strategy_name].get("cost_euros", 0) for strategy_name in strategies]
    ax.bar(names, costs, color=["#2ecc71", "#3498db", "#9b59b6", "#e74c3c"])
    ax.set_ylabel("Coût (€)")
    ax.set_title("Coût total estimé")

    plt.tight_layout()
    output_path = Path(__file__).parent.parent / "results" / "day4_comparison.png"
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    print(f"Graphique enregistré : {output_path}")

if __name__ == "__main__":
    main()
