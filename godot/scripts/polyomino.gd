extends Node2D

var id = null
var on_positions = []

func _ready():
	$grid.create(on_positions)

func _enter_tree():
	rotation = 0.0
	scale = Vector2(1.0, 1.0)	
	
func copy(other):
	id = other.id
	on_positions = other.on_positions.duplicate()
