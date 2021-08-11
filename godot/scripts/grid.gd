extends TileMap

#onready var tile_size = null
#onready var half_tile_size = null
#
#onready var grid_size = null
#onready var tile_class = null

#onready var grid = []


func _ready():
	pass

func create(on_positions, on_tile):
	for pos in on_positions:
		var instance = on_tile.instance()
		instance.global_position = map_to_world(pos) # + Vector2(7, 7)
		add_child(instance)
