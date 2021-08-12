extends TileMap

var Monomino = preload("res://scenes/monomino.tscn")

func create(on_positions):
	for pos in on_positions:
		var instance = Monomino.instance()
		instance.global_position = map_to_world(pos)
		add_child(instance)
