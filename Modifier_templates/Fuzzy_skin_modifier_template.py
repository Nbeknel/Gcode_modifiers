## FUZZY SKIN MODIFIER TEMPLATE ##
#
# Input:
#
# coords_start
#   x,y-coordinate pair from which the current extruded line starts,
#   relative to the center of the bounding box of the current object;
#
# coords_end
#   x,y-coordinate pair at which the current extruded line ends,
#   relative to the center of the bounding box of the current object;
#
# z
#   absolute z-coordinate of the middle of the current extruded line
#   {layer_z - 0.5 * layer_height};
#
# feature_type
#   current feature type, same as the names of feature types listed when
#   viewing the file in a g-code viewer,
#   e.g. "Internal Perimeter" (SuperSlicer), "Perimeter" (PrusaSlicer).
#
#
# Output:
# 
# Must be a list of tuples, always.
# Each tuple must consist of three parameters, always.
#
# first entry:
#   type: float
#   value: between 0 and 1, 1 included, it is best to exclude 0
#   defines how far along the line fuzzy skin should be applied or not,
#   with 0 at the start and 1 at the end of the line
#
# second entry:
#   type: bool
#   defines whether or not to apply fuzzy skin to the current segment,
#   True - apply fuzzy skin, False - don't apply fuzzy skin
#
# third entry:
#   type: int
#   DEFAULT, INWARDS or OUTWARDS as defined below
#   DEFAULT applies fuzzy skin as would the slicer, i.e. on both sides of
#       the current line
#   INSIDE applies fuzzy skin moving the offset points into the model,
#       might be helpful if you want to keep model accuracy or tolerances
#   OUTSIDE applies fuzzy skin moving the offset points away from the
#       model, making that part of the model thicker
#
# The list must be sorted in ascending order with regards to the first
# entry. The final tuple must contain 1 in its first entry.
#
# Example:
# return [(0.5, False, DEFAULT), (1, True, OUTWARDS)]
# will make it so that for each line, the first half would be printed is
# normal, while the second half will have fuzzy skin applied to it.

Condition = tuple[float, bool, int]

INWARDS = -1
DEFAULT = 0
OUTWARDS = 1

def fuzzy_skin_conditions(coords_start: list, coords_end: list, z: float, feature_type: str) -> list[Condition]:
    return [(1, False, DEFAULT)]