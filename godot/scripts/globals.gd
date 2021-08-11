extends Node

const DEBUG_MODE = true

# layer bitmask values
const BOUNDARY_LAYER = 1
const OBJECT_LAYER = 2

##############################
# action execution constants #
##############################
const LINEAR_DELTA = 1 # change in pixels - used for linear translations
const ANGULAR_DELTA = 2.0  # change in degrees - used for rotational actions
const SCALE_DELTA = Vector2(0.1, 0.1) # change in scale - used for zooming operations

# for translation operations
const MIN_X = -1000.0
const MAX_X = 1000.0
const MIN_Y = -1000.0
const MAX_Y = 1000.0

# for scaling operations
const MIN_SCALE = Vector2(1.0, 1.0)
const MAX_SCALE = Vector2(3.0, 3.0)
const DEFAULT_SCALE = Vector2(2.0, 2.0)
