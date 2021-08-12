# GDScript: environment.gd

extends Node2D

# a queue of actions that are pending execution
onready var pending_actions = []

# only a single piece can be active at one time
onready var active_object = null


###################################
# Godot-AI-Bridge (GAB) Variables #
###################################
#onready var gab = $GabLib  # library reference
#onready var gab_options = {
#	'publisher_port': 10003, # specifies alternate port - default port is 10001
#	'listener_port': 10004, # specifies alternate port - default port is 10002
#
#	# supported socket options (for advanced users - see ZeroMQ documentation for details)
#	'socket_options': {
#		'ZMQ_RCVHWM': 10,  # receive highwater mark
#		'ZMQ_RCVTIMEO': 50,  # timeout on receive I/O blocking
#		'ZMQ_SNDHWM': 10,  # send highwater mark
#		'ZMQ_SNDTIMEO': 50,  # timeout on send I/O blocking
#		'ZMQ_CONFLATE': 0  # only keep last message in send/receive queues (others are dropped)
#	},
#
#	# controls Godot-AI-Bridge's console verbosity level (larger numbers -> greater verbosity)
#	'verbosity': 3   # supported values (-1=FATAL; 0=ERROR; 1=WARNING; 2=INFO; 3=DEBUG; 4=TRACE)
#}

#onready var Monomino = preload("res://scenes/monomino.tscn")
#onready var grid = $polyomino

func _ready():
	pass
	# initialize Godot-AI-Bridge
#	gab.connect(gab_options)

	# initializes a timer that controls the frequency of environment state broadcasts
#	_create_publish_timer(0.1)

func _input(event):	
	if event.is_action_pressed("ui_up"):
		add_action('up')
	elif event.is_action_pressed("ui_down"):
		add_action('down')
	elif event.is_action_pressed("ui_left"):
		add_action('left')
	elif event.is_action_pressed("ui_right"):
		add_action('right')
	elif event.is_action_pressed("ui_rotate_clockwise"):
		add_action('rotate_clockwise')
	elif event.is_action_pressed("ui_rotate_counterclockwise"):
		add_action('rotate_counterclockwise')
	elif event.is_action_pressed("ui_zoom_in"):
		add_action('zoom_in')
	elif event.is_action_pressed("ui_zoom_out"):
		add_action('zoom_out')
	elif event.is_action_pressed("ui_next_shape"):
		add_action('next_shape')		

#func _create_publish_timer(wait_time):
#	var publish_timer = Timer.new()
#
#	publish_timer.wait_time = wait_time  
#	publish_timer.connect("timeout", self, "_on_publish_state")
#	add_child(publish_timer)
#	publish_timer.start()




func _process(_delta):
	
	# removes and executes the oldest pending action from the queue (if one exists)
	var action = pending_actions.pop_front()
	if action:
		execute(action)

# adds an action to the agent's pending_actions queue for later execution
func add_action(action):
	if Globals.DEBUG_MODE:
		print('adding action: ', action)
		
	pending_actions.push_back(action)

# executes an action
func execute(action):
	if Globals.DEBUG_MODE:
		print('executing action: ', action)
		
	match action:
		'up', 'down', 'left', 'right': execute_translation(action)
		'rotate_clockwise', 'rotate_counterclockwise': execute_rotation(action)
		'zoom_in', 'zoom_out': execute_zoom(action)
		'next_shape': execute_next_shape()
				
		# default case: unrecognized action
		_: print('unrecogized action: ', action)

func execute_next_shape():
	
	var id = 0 if (active_object == null) else (active_object.id + 1) % Globals.N_PENTOMINOS
			
	var shape = Globals.PENTOMINOS[id].duplicate()
	shape.global_position = Vector2(64, 64)	
	
	if active_object != null:
		remove_child(active_object)
		
	add_child(shape)
	active_object = shape
	
func execute_translation(action):
	
	match action:	
		'up': active_object.global_position.y -= Globals.LINEAR_DELTA
		'down': active_object.global_position.y += Globals.LINEAR_DELTA
		'left': active_object.global_position.x -= Globals.LINEAR_DELTA
		'right': active_object.global_position.x += Globals.LINEAR_DELTA

		# default case: unrecognized translation
		_: print('unrecogized translation: ', action)

func execute_rotation(action):
	match action:
		'rotate_clockwise': active_object.rotation_degrees += Globals.ANGULAR_DELTA
		'rotate_counterclockwise': active_object.rotation_degrees -= Globals.ANGULAR_DELTA
		
		# default case: unrecognized rotation
		_: print('unrecogized rotation: ', action)

func execute_zoom(action):
	var new_scale = null
	
	match action:
		'zoom_in': new_scale = active_object.scale + Globals.SCALE_DELTA
		'zoom_out': new_scale = active_object.scale - Globals.SCALE_DELTA
		
		# default case: unrecognized zoom
		_: print('unrecogized zoom: ', action)

	if new_scale < Globals.MIN_SCALE:
		new_scale = Globals.MIN_SCALE
	elif new_scale > Globals.MAX_SCALE:
		new_scale = Globals.MAX_SCALE
		
	active_object.scale = new_scale

#######################
### SIGNAL HANDLERS ###
#######################

# signal handler for publish_timer's "timeout" signal
#func _on_publish_state():
#	for agent in $Agents.get_children():
#
#		# topics characterize message content. recipients can use topics to filter messages (e.g., by agent id)
#		var topic = '/polyomino/agent/%s' % agent.id
#
#		# Godot-AI-Bridge wraps this state into the "data" element of a JSON-encoded message. messages are also
#		# given a "header" element containing a unique sequence numbers (seqno) and timestamp in milliseconds
#		var msg = agent.get_state()
#
#		# broadcasts the message to all clients
#		gab.send(topic, msg)
	
# signal handler for Godot-AI-Bridge's "event_requested" signal
#func _on_event_requested(event_details):
#	print('Godot Environment: event request received -> "%s"' % event_details)
#
#	var event = event_details['data']['event']	
#	match event['type']:
#		'action':
#			# apply action to all agents with matching id
#			for agent in $Agents.get_children():
#				# adds action to an agent's pending action queue
#				if event['agent'] == agent.id:				
#					agent.add_action(event['value'])
#
#		# default case: unrecognized actions
#		_: print('unrecogized event type: ', event['type']) 
