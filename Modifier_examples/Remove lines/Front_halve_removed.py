Condition = tuple[float, bool]

def print_conditions(coords_start: list, coords_end: list, z: float, feature_type: str) -> list[Condition]:
    boundary = 0
    if coords_start[1] < boundary:
        if coords_end[1] < boundary:
            return [(1, False)]
        return [((boundary - coords_start[1])/(coords_end[1] - coords_start[1]), False), (1, True)]
    if coords_end[1] >= boundary:
        return [(1, True)]
    return [((boundary - coords_start[1])/(coords_end[1] - coords_start[1]), True), (1, False)]