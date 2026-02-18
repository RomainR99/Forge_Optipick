def build_zone_map(warehouse):
    zone_map = {}
    for zone, data in warehouse["zones"].items():
        for coord in data["coords"]:
            zone_map[tuple(coord)] = zone
    return zone_map
