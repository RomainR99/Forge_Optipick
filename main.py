import json
from pathlib import Path

from src.loader import load_data
from src.build_data import build_minizinc_data
from src.solver import solve_allocation_minizinc
from src.postprocess import assignment_to_allocation
from src.metrics import compute_basic_metrics

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)


def main():
    orders, agents, products, warehouse = load_data()

    data, order_ids, agent_ids, unassigned = build_minizinc_data(
        orders, agents, products, warehouse
    )

    sol = solve_allocation_minizinc(data, time_limit_ms=8000)

    allocation = assignment_to_allocation(sol["assign"], order_ids, agent_ids)
    metrics = compute_basic_metrics(allocation, orders, products)

    # Print simple
    for aid, oids in allocation.items():
        print(f"{aid} -> {oids}")

    # Exports
    (RESULTS_DIR / "allocation.json").write_text(
        json.dumps(allocation, indent=2), encoding="utf-8"
    )
    (RESULTS_DIR / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    (RESULTS_DIR / "unassigned_orders.json").write_text(
        json.dumps(unassigned, indent=2), encoding="utf-8"
    )

    print("\n✅ Exports:")
    print(" - results/allocation.json")
    print(" - results/metrics.json")
    print(" - results/unassigned_orders.json")


if __name__ == "__main__":
    main()
