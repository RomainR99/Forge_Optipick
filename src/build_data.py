from src.utils import build_zone_map

def build_minizinc_data(orders, agents, products, warehouse):
    product_map = {p["id"]: p for p in products}
    zone_map = build_zone_map(warehouse)

    order_ids = [o["id"] for o in orders]
    agent_ids = [a["id"] for a in agents]

    order_weight = []
    order_volume = []
    order_has_fragile = []
    order_has_zoneC = []

    for o in orders:
        w = 0.0
        v = 0.0
        has_fragile = 0
        has_zoneC = 0

        for it in o["items"]:
            p = product_map[it["product_id"]]
            qty = it["quantity"]

            w += p["weight"] * qty
            v += p["volume"] * qty

            if p.get("fragile", False):
                has_fragile = 1

            loc = tuple(p["location"])
            if zone_map.get(loc) == "C":
                has_zoneC = 1

        order_weight.append(int(round(w * 100)))
        order_volume.append(int(round(v * 100)))
        order_has_fragile.append(has_fragile)
        order_has_zoneC.append(has_zoneC)

    agent_cap_weight = [int(round(a["capacity_weight"] * 100)) for a in agents]
    agent_cap_volume = [int(round(a["capacity_volume"] * 100)) for a in agents]
    agent_is_robot = [1 if a["type"] == "robot" else 0 for a in agents]

    data = {
        "N_ORDERS": len(orders),
        "N_AGENTS": len(agents),
        "order_weight": order_weight,
        "order_volume": order_volume,
        "order_has_fragile": order_has_fragile,
        "order_has_zoneC": order_has_zoneC,
        "agent_cap_weight": agent_cap_weight,
        "agent_cap_volume": agent_cap_volume,
        "agent_is_robot": agent_is_robot,
    }

    return data, order_ids, agent_ids
