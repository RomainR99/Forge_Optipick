def build_zone_map(warehouse):
    zone_map = {}
    for zone, data in warehouse["zones"].items():
        for coord in data["coords"]:
            zone_map[tuple(coord)] = zone
    return zone_map


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def nearest_neighbor_distance(entry, locations):
    """
    Heuristique simple : entrée -> plus proche -> ... -> retour entrée
    Sert uniquement à estimer un temps (C5).
    """
    if not locations:
        return 0

    remaining = set(locations)
    current = entry
    dist = 0

    while remaining:
        nxt = min(remaining, key=lambda p: manhattan(current, p))
        dist += manhattan(current, nxt)
        current = nxt
        remaining.remove(nxt)

    dist += manhattan(current, entry)
    return dist


def parse_hhmm_to_seconds(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return (int(h) * 3600) + (int(m) * 60)
