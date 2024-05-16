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
# Each tuple must consist of two parameters, always.
#
# first entry:
#   type: float
#   value: between 0 and 1, 1 included, it is best to exclude 0
#   defines how far along the line it should be printed or not, with 0 at
#   the start and 1 at the end of the line
#
# second entry:
#   type: bool
#   defines whether or not to print the current segment,
#   True - print, False - don't print
#
# The list must be sorted in ascending order with regards to the first
# entry. The final tuple must contain 1 in its first entry.
#
# Example:
# return [(0.5, True), (1, False)]
# will make it so that for each line, the first half would be printed,
# while the second half won't be printed.

Condition = tuple[float, bool]

def fuzzy_skin_conditions(coords_start: list, coords_end: list, z: float, feature_type: str) -> list[Condition]:
    return [(1, True)]