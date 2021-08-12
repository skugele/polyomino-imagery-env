extends Node2D

var Monomino = preload("res://scenes/monomino.tscn")

var id = 1

# Called when the node enters the scene tree for the first time.
func _ready():
	$grid.create([], Monomino)

func create(on_positions):
	$grid.create(on_positions, Monomino)
