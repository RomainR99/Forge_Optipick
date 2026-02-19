from src.utils import build_zone_map, nearest_neighbor_distance, parse_hhmm_to_seconds

PICK_SEC_PER_ITEM = 30
ROBOT_MAX_ITEM_WEIGHT = 10.0  # kg (C3)


def build_minizinc_data(orders, agents, products, warehouse):
    product_map = {p["id"]: p for p in products}
    zone_map = build_zone_map(warehouse)
    entry = tuple(warehouse["entry_point"])

    order_ids = []
    kept_orders = []  # commandes gardées (compatibles)
    unassigned = []   # commandes rejetées (C2)

    # ---- Filtre C2 (incompatibilités) au niveau commande
    for o in orders:
        item_pids = [it["product_id"] for it in o["items"]]
        item_set = set(item_pids)

        incompatible = False
        for pid in item_set:
            inc_list = product_map[pid].get("incompatible_with", [])
            # si un des incompatibles est aussi présent dans la commande => incompatible
            if any(inc in item_set for inc in inc_list):
                incompatible = True
                break

        if incompatible:
            unassigned.append({
                "order_id": o["id"],
                "reason": "C2_incompatible_products"
            })
        else:
            kept_orders.append(o)
            order_ids.append(o["id"])

    agent_ids = [a["id"] for a in agents]

    # ---- Construire tableaux commandes
    order_weight = []
    order_volume = []
    order_has_fragile = []
    order_has_zoneC = []
    order_has_heavy_item = []
    order_is_incompatible = []  # ici toujours 0 pour les kept_orders
    order_slack_sec = []

    # Pour C5 : matrice temps_need[o][a]
    time_need_sec = []

    for o in kept_orders:
        w = 0.0
        v = 0.0
        has_fragile = 0
        has_zoneC = 0
        has_heavy = 0
        locations = []
        total_items = 0

        for it in o["items"]:
            p = product_map[it["product_id"]]
            qty = it["quantity"]

            w += p["weight"] * qty
            v += p["volume"] * qty
            total_items += qty

            if p.get("fragile", False):
                has_fragile = 1

            if p["weight"] > ROBOT_MAX_ITEM_WEIGHT:
                has_heavy = 1

            loc = tuple(p["location"])
            locations.append(loc)
            if zone_map.get(loc) == "C":
                has_zoneC = 1

        dist = nearest_neighbor_distance(entry, locations)

        # Slack (deadline - received) en secondes (C5)
        recv = parse_hhmm_to_seconds(o["received_time"])
        ddl = parse_hhmm_to_seconds(o["deadline"])
        slack = max(0, ddl - recv)

        order_weight.append(int(round(w * 100)))
        order_volume.append(int(round(v * 100)))
        order_has_fragile.append(has_fragile)
        order_has_zoneC.append(has_zoneC)
        order_has_heavy_item.append(has_heavy)
        order_is_incompatible.append(0)
        order_slack_sec.append(int(slack))

        # Matrice temps_need pour chaque agent
        row = []
        for a in agents:
            speed = float(a["speed"])
            travel_sec = int(round(dist / speed)) if speed > 0 else 10**9
            pick_sec = total_items * PICK_SEC_PER_ITEM
            row.append(int(travel_sec + pick_sec))
        time_need_sec.append(row)

    # ---- Agents
    agent_cap_weight = [int(round(a["capacity_weight"] * 100)) for a in agents]
    agent_cap_volume = [int(round(a["capacity_volume"] * 100)) for a in agents]
    agent_is_robot = [1 if a["type"] == "robot" else 0 for a in agents]

    data = {
        "N_ORDERS": len(kept_orders),
        "N_AGENTS": len(agents),

        "order_weight": order_weight,
        "order_volume": order_volume,
        "order_has_fragile": order_has_fragile,
        "order_has_zoneC": order_has_zoneC,
        "order_has_heavy_item": order_has_heavy_item,
        "order_is_incompatible": order_is_incompatible,
        "order_slack_sec": order_slack_sec,

        "agent_cap_weight": agent_cap_weight,
        "agent_cap_volume": agent_cap_volume,
        "agent_is_robot": agent_is_robot,

        "time_need_sec": time_need_sec,
    }

    return data, order_ids, agent_ids, unassigned
