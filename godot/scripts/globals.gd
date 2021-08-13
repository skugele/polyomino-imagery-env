extends Node

const DEBUG_MODE = false

# layer bitmask values
const BOUNDARY_LAYER = 1
const OBJECT_LAYER = 2

const PUBLISH_NO_CHANGE_TIMEOUT = 10.0

##############################
# action execution constants #
##############################
const LINEAR_DELTA = 4 # change in pixels - used for linear translations
const ANGULAR_DELTA = 6  # change in degrees - used for rotational actions
const SCALE_DELTA = Vector2(0.1, 0.1) # change in scale - used for zooming operations

# for translation operations
const MIN_X = -1000.0
const MAX_X = 1000.0
const MIN_Y = -1000.0
const MAX_Y = 1000.0

# for scaling operations
const MIN_SCALE = Vector2(0.65, 0.65)
const MAX_SCALE = Vector2(1.4, 1.4)
const DEFAULT_SCALE = Vector2(2.0, 2.0)

enum SHAPES {TROMINOS = 1, 
			 TETROMINOS, 
			 PENTOMINOS}

const N_PENTOMINOS = 18
const N_TETROMINOS = 7
const N_TROMINOS = 2

onready var _PENTOMINOS = []
onready var _TETROMINOS = []
onready var _TROMINOS = []

const POLYOMINO_SCENE = preload("res://scenes/polyomino.tscn")

func _ready():
	_create_trominos()
	_create_tetrominos()
	_create_pentominos()
	
func _create_trominos():
	pass
	
func _create_tetrominos():
	pass
	
func _create_pentominos():
	
	# initialize polyominos
	for p in range(N_PENTOMINOS):
		var instance = POLYOMINO_SCENE.instance()
		instance.id = p
		instance.shape = SHAPES.PENTOMINOS
		_PENTOMINOS.append(instance) 
		
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2   X X X    #
	#  3       X    #
	#  4            #
	################
	_PENTOMINOS[0].on_positions = [
		Vector2(2, 1),
		Vector2(1, 2), Vector2(2, 2), Vector2(3, 2),
		Vector2(3, 3),
	]

	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2   X X X    #
	#  3   X        #
	#  4            #
	#################
	_PENTOMINOS[1].on_positions = [
		Vector2(2, 1),
		Vector2(1, 2), Vector2(2, 2), Vector2(3, 2),
		Vector2(1, 3),
	]
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X      #
	#  3     X      #
	#  4     X X    #
	#################
	_PENTOMINOS[2].on_positions = [
		Vector2(2, 1),
		Vector2(2, 2),
		Vector2(2, 3),
		Vector2(2, 4), Vector2(3, 4),
	]
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X      #
	#  3     X      #
	#  4   X X      #
	#################
	_PENTOMINOS[3].on_positions = [
		Vector2(2, 1),
		Vector2(2, 2),
		Vector2(2, 3),
		Vector2(2, 4), Vector2(1, 4),
	]

	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2   X X      #
	#  3   X X      #
	#  4            #
	#################
	_PENTOMINOS[4].on_positions = [
		Vector2(2, 1),
		Vector2(1, 2), Vector2(2, 2),
		Vector2(1, 3), Vector2(2, 3),
	]
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X X    #
	#  3     X X    #
	#  4            #
	#################
	_PENTOMINOS[5].on_positions = [
		Vector2(2, 1),
		Vector2(2, 2), Vector2(3, 2), 
		Vector2(2, 3), Vector2(3, 3),
	]

	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X      #
	#  3   X X      #
	#  4   X        #
	#################
	_PENTOMINOS[6].on_positions = [
		Vector2(2, 1),
		Vector2(2, 2), 
		Vector2(1, 3), Vector2(2, 3), 
		Vector2(1, 4),
	]

	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X      #
	#  3     X X    #
	#  4       X    #
	#################
	_PENTOMINOS[7].on_positions = [
		Vector2(2, 1),
		Vector2(2, 2), 
		Vector2(2, 3), Vector2(3, 3), 
		Vector2(3, 4),
	]
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2   X X      #
	#  3     X      #
	#  4     X      #
	#################
	_PENTOMINOS[8].on_positions = [
		Vector2(2, 1),
		Vector2(1, 2), Vector2(2, 2), 
		Vector2(2, 3),
		Vector2(2, 4),
	]
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X X    #
	#  3     X      #
	#  4     X      #
	#################
	_PENTOMINOS[9].on_positions = [
		Vector2(2, 1),
		Vector2(2, 2), Vector2(3, 2), 
		Vector2(2, 3),
		Vector2(2, 4),
	]
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X X    #
	#  2     X      #
	#  3   X X      #
	#  4            #
	#################
	_PENTOMINOS[10].on_positions = [
		Vector2(2, 1), Vector2(3, 1),
		Vector2(2, 2),
		Vector2(1, 3), Vector2(2, 3),
	]

	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1   X X      #
	#  2     X      #
	#  3     X X    #
	#  4            #
	#################
	_PENTOMINOS[11].on_positions = [
		Vector2(1, 1), Vector2(2, 1),
		Vector2(2, 2),
		Vector2(2, 3), Vector2(3, 3),
	]
	
	
	#################
	#    0 1 2 3 4  #
	#  0     X      # 
	#  1     X      #
	#  2     X      #
	#  3     X      #
	#  4     X      #
	#################
	_PENTOMINOS[12].on_positions = [
		Vector2(2, 0), 
		Vector2(2, 1),
		Vector2(2, 2),
		Vector2(2, 3), 
		Vector2(2, 4),
	]
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X      #
	#  3   X X X    #
	#  4            #
	#################
	_PENTOMINOS[13].on_positions = [
		Vector2(2, 1), 
		Vector2(2, 2),
		Vector2(1, 3),	Vector2(2, 3), 	Vector2(3, 3),
	]
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1   X   X    #
	#  2   X X X    #
	#  3            #
	#  4            #
	#################
	_PENTOMINOS[14].on_positions = [
		Vector2(1, 1), Vector2(3, 1), 
		Vector2(1, 2),	Vector2(2, 2), 	Vector2(3, 2),
	]

	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X      #
	#  3 X X X      #
	#  4            #
	#################
	_PENTOMINOS[15].on_positions = [
		Vector2(2, 1), 
		Vector2(2, 2), 
		Vector2(0, 3),	Vector2(1, 3), 	Vector2(2, 3),
	]

	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1       X    #
	#  2     X X    #
	#  3   X X      #
	#  4            #
	#################
	_PENTOMINOS[16].on_positions = [
		Vector2(3, 1), 
		Vector2(2, 2), Vector2(3, 2), 
		Vector2(1, 3),	Vector2(2, 3),
	]

	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2   X X X    #
	#  3     X      #
	#  4            #
	#################
	_PENTOMINOS[17].on_positions = [
		Vector2(2, 1), 
		Vector2(1, 2), Vector2(2, 2), Vector2(3, 2), 
		Vector2(2, 3),
	]

func get_object(shape, id):
	var object = POLYOMINO_SCENE.instance()
	
	match shape:
		SHAPES.TROMINOS: pass
		SHAPES.TETROMINOS: pass
		SHAPES.PENTOMINOS:
			object.copy(_PENTOMINOS[id])
		
		_: print('unrecognized shape: ', shape)
			
	return object
