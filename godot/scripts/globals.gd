extends Node

const DEBUG_MODE = true

# layer bitmask values
const BOUNDARY_LAYER = 1
const OBJECT_LAYER = 2

##############################
# action execution constants #
##############################
const LINEAR_DELTA = 5 # change in pixels - used for linear translations
const ANGULAR_DELTA = 5  # change in degrees - used for rotational actions
const SCALE_DELTA = Vector2(0.1, 0.1) # change in scale - used for zooming operations

# for translation operations
const MIN_X = -1000.0
const MAX_X = 1000.0
const MIN_Y = -1000.0
const MAX_Y = 1000.0

# for scaling operations
const MIN_SCALE = Vector2(0.8, 0.8)
const MAX_SCALE = Vector2(1.5, 1.5)
const DEFAULT_SCALE = Vector2(2.0, 2.0)

const N_PENTOMINOS = 18
onready var PENTOMINOS = []

const N_TETROMINOS = 7
onready var TETROMINOS = []

const N_TROMINOS = 2
onready var TROMINOS

func _ready():
	create_pentominos()

func create_pentominos():
	var Polyomino = preload("res://scenes/polyomino.tscn")
	
	# initialize polyominos
	for p in range(N_PENTOMINOS):
		var instance = Polyomino.instance()
		instance.id = p
		PENTOMINOS.append(instance) 
		
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2   X X X    #
	#  3       X    #
	#  4            #
	################
	PENTOMINOS[0].create([
		Vector2(2, 1),
		Vector2(1, 2), Vector2(2, 2), Vector2(3, 2),
		Vector2(3, 3),
	])

	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2   X X X    #
	#  3   X        #
	#  4            #
	#################
	PENTOMINOS[1].create([
		Vector2(2, 1),
		Vector2(1, 2), Vector2(2, 2), Vector2(3, 2),
		Vector2(1, 3),
	])
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X      #
	#  3     X      #
	#  4     X X    #
	#################
	PENTOMINOS[2].create([
		Vector2(2, 1),
		Vector2(2, 2),
		Vector2(2, 3),
		Vector2(2, 4), Vector2(3, 4),
	])
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X      #
	#  3     X      #
	#  4   X X      #
	#################
	PENTOMINOS[3].create([
		Vector2(2, 1),
		Vector2(2, 2),
		Vector2(2, 3),
		Vector2(2, 4), Vector2(1, 4),
	])

	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2   X X      #
	#  3   X X      #
	#  4            #
	#################
	PENTOMINOS[4].create([
		Vector2(2, 1),
		Vector2(1, 2), Vector2(2, 2),
		Vector2(1, 3), Vector2(2, 3),
	])
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X X    #
	#  3     X X    #
	#  4            #
	#################
	PENTOMINOS[5].create([
		Vector2(2, 1),
		Vector2(2, 2), Vector2(3, 2), 
		Vector2(2, 3), Vector2(3, 3),
	])

	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X      #
	#  3   X X      #
	#  4   X        #
	#################
	PENTOMINOS[6].create([
		Vector2(2, 1),
		Vector2(2, 2), 
		Vector2(1, 3), Vector2(2, 3), 
		Vector2(1, 4),
	])

	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X      #
	#  3     X X    #
	#  4       X    #
	#################
	PENTOMINOS[7].create([
		Vector2(2, 1),
		Vector2(2, 2), 
		Vector2(2, 3), Vector2(3, 3), 
		Vector2(3, 4),
	])
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2   X X      #
	#  3     X      #
	#  4     X      #
	#################
	PENTOMINOS[8].create([
		Vector2(2, 1),
		Vector2(1, 2), Vector2(2, 2), 
		Vector2(2, 3),
		Vector2(2, 4),
	])
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X X    #
	#  3     X      #
	#  4     X      #
	#################
	PENTOMINOS[9].create([
		Vector2(2, 1),
		Vector2(2, 2), Vector2(3, 2), 
		Vector2(2, 3),
		Vector2(2, 4),
	])
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X X    #
	#  2     X      #
	#  3   X X      #
	#  4            #
	#################
	PENTOMINOS[10].create([
		Vector2(2, 1), Vector2(3, 1),
		Vector2(2, 2),
		Vector2(1, 3), Vector2(2, 3),
	])

	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1   X X      #
	#  2     X      #
	#  3     X X    #
	#  4            #
	#################
	PENTOMINOS[11].create([
		Vector2(1, 1), Vector2(2, 1),
		Vector2(2, 2),
		Vector2(2, 3), Vector2(3, 3),
	])
	
	
	#################
	#    0 1 2 3 4  #
	#  0     X      # 
	#  1     X      #
	#  2     X      #
	#  3     X      #
	#  4     X      #
	#################
	PENTOMINOS[12].create([
		Vector2(2, 0), 
		Vector2(2, 1),
		Vector2(2, 2),
		Vector2(2, 3), 
		Vector2(2, 4),
	])
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X      #
	#  3   X X X    #
	#  4            #
	#################
	PENTOMINOS[13].create([
		Vector2(2, 1), 
		Vector2(2, 2),
		Vector2(1, 3),	Vector2(2, 3), 	Vector2(3, 3),
	])
	
	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1   X   X    #
	#  2   X X X    #
	#  3            #
	#  4            #
	#################
	PENTOMINOS[14].create([
		Vector2(1, 1), Vector2(3, 1), 
		Vector2(1, 2),	Vector2(2, 2), 	Vector2(3, 2),
	])

	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2     X      #
	#  3 X X X      #
	#  4            #
	#################
	PENTOMINOS[15].create([
		Vector2(2, 1), 
		Vector2(2, 2), 
		Vector2(0, 3),	Vector2(1, 3), 	Vector2(2, 3),
	])

	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1       X    #
	#  2     X X    #
	#  3   X X      #
	#  4            #
	#################
	PENTOMINOS[16].create([
		Vector2(3, 1), 
		Vector2(2, 2), Vector2(3, 2), 
		Vector2(1, 3),	Vector2(2, 3),
	])

	#################
	#    0 1 2 3 4  #
	#  0            # 
	#  1     X      #
	#  2   X X X    #
	#  3     X      #
	#  4            #
	#################
	PENTOMINOS[17].create([
		Vector2(2, 1), 
		Vector2(1, 2), Vector2(2, 2), Vector2(3, 2), 
		Vector2(2, 3),
	])
