Condition = tuple[float, bool, int]

INWARDS = -1
DEFAULT = 0
OUTWARDS = 1

DIRECTION = INWARDS

def fuzzy_skin_conditions(coords_start: list, coords_end: list, z: float, feature_type: str) -> list[Condition]:
    if feature_type not in ["External perimeter", "Overhang perimeter"]:
        return [(1, False, DIRECTION)]
    boundary = 0
    if coords_start[1] < boundary:
        if coords_end[1] < boundary:
            return [(1, True, DIRECTION)]
        return [((boundary - coords_start[1])/(coords_end[1] - coords_start[1]), True, DIRECTION), (1, False, DIRECTION)]
    if coords_end[1] >= boundary:
        return [(1, False, DIRECTION)]
    return [((boundary - coords_start[1])/(coords_end[1] - coords_start[1]), False, DIRECTION), (1, True, DIRECTION)]