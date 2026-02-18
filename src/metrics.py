def compute_basic_metrics(allocation, orders, products):
    product_map = {p["id"]: p for p in products}
    orders_map = {o["id"]: o for o in orders}

    rows = []
    for agent_id, order_ids in allocation.items():
        total_w = 0.0
        total_v = 0.0
        for oid in order_ids:
            o = orders_map[oid]
            for it in o["items"]:
                p = product_map[it["product_id"]]
                qty = it["quantity"]
                total_w += p["weight"] * qty
                total_v += p["volume"] * qty

        rows.append({
            "agent": agent_id,
            "orders": len(order_ids),
            "weight": round(total_w, 2),
            "volume": round(total_v, 2),
        })

    return rows
