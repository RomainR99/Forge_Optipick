import json
from pathlib import Path

DATA_DIR = Path("data")

def load_data():
    with open(DATA_DIR / "orders.json") as f:
        orders = json.load(f)
    with open(DATA_DIR / "agents.json") as f:
        agents = json.load(f)
    with open(DATA_DIR / "products.json") as f:
        products = json.load(f)
    with open(DATA_DIR / "warehouse.json") as f:
        warehouse = json.load(f)
    return orders, agents, products, warehouse
