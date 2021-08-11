extends Node2D

onready var is_flipped = false

onready var Monomino = preload("res://scenes/monomino.tscn")

onready var grid = $grid

# Called when the node enters the scene tree for the first time.
func _ready():

	var on_positions = [
		Vector2(2, 1),
		Vector2(1, 2), Vector2(2, 2), Vector2(3, 2),
		Vector2(3, 3),
	]
	
	grid.create(on_positions, Monomino)
	
	# randomize flip
	
	# if flipped, set is_flipped == true
	
	# randomize rotation
	
# reflects the object along its horizontal axis
func flip():
	pass

func randomize_rotatation():
	pass
	
	
# Called every frame. 'delta' is the elapsed time since the previous frame.
#func _process(delta):
#	pass
