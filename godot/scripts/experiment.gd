# GDScript: environment.gd

extends Node2D

# a queue of actions that are pending execution
onready var pending_actions = []

# only a single piece can be active at one time
onready var active_object = null

# timer for state (e.g., screenshot) publication to clients
var publish_timer = Timer.new()

###################################
# Godot-AI-Bridge (GAB) Variables #
###################################
onready var gab = $GabLib  # library reference
onready var gab_options = {
	'publisher_port': 10001, # specifies alternate port - default port is 10001
	'listener_port': 10002, # specifies alternate port - default port is 10002

	# supported socket options (for advanced users - see ZeroMQ documentation for details)
	'socket_options': {
		'ZMQ_RCVHWM': 10,  # receive highwater mark
		'ZMQ_RCVTIMEO': 50,  # timeout on receive I/O blocking
		'ZMQ_SNDHWM': 10,  # send highwater mark
		'ZMQ_SNDTIMEO': 50,  # timeout on send I/O blocking
		'ZMQ_CONFLATE': 0  # only keep last message in send/receive queues (others are dropped)
	},

	# controls Godot-AI-Bridge's console verbosity level (larger numbers -> greater verbosity)
	'verbosity': 4   # supported values (-1=FATAL; 0=ERROR; 1=WARNING; 2=INFO; 3=DEBUG; 4=TRACE)
}

# state variable for tracking object-boundary collisions
onready var boundary_collisions = 0

onready var unpublished_change = true

func _ready():

	# this line was added to remove extra "border" lines appearing in screenshots. 
	# screenshot dimensions were 130x128!
	get_viewport().size = Vector2(ProjectSettings.get_setting("display/window/size/width"),
								  ProjectSettings.get_setting("display/window/size/height")) 

	# initialize Godot-AI-Bridge
	gab.connect(gab_options)

	# initializes a timer that controls the frequency of environment state broadcasts
	publish_timer.wait_time = Globals.PUBLISH_NO_CHANGE_TIMEOUT
	publish_timer.connect("timeout", self, "_on_publish_state")
	add_child(publish_timer)
	

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


# removes and executes the oldest pending action from the queue (if one exists)
func _process(_delta):	
	if unpublished_change:
		publish_state()
			
	# move active objects towards centroid in the event of a collision
	if boundary_collisions > 0:
		var curr_pos = active_object.global_position
		var safe_pos = $centroid.global_position
		
		active_object.global_position = curr_pos.move_toward(safe_pos, Globals.LINEAR_DELTA)
	else:
		var action = pending_actions.pop_front()
		if action:
			
			# activity - stop time-based publication
			if not publish_timer.is_stopped():
				publish_timer.stop()
				
			execute(action)
			unpublished_change = true
		else:
			
			# inactivity - begin time-based publication
			if publish_timer.is_stopped():
				publish_timer.start()


# adds an action to the agent's pending_actions queue for later execution
func add_action(action):
	if Globals.DEBUG_MODE:
		print('adding action: ', action)
		
	pending_actions.push_back(action)


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
	var id = 0
	
	# pentominos specific
	if active_object != null:
		id = (active_object.id + 1) % Globals.N_PENTOMINOS
		remove_child(active_object)

	active_object = Globals.get_object(Globals.SHAPES.PENTOMINOS, id)
	active_object.global_position = $centroid.global_position

	add_child(active_object)

	# tetrominos specific
#	if active_object != null:
#		id = (active_object.id + 1) % Globals.N_TETROMINOS
#		remove_child(active_object)
#
#	active_object = Globals.get_object(Globals.SHAPES.TETROMINOS, id)
#	active_object.global_position = $centroid.global_position
#
#	add_child(active_object)
	
	# trominos specific
#	if active_object != null:
#		id = (active_object.id + 1) % Globals.N_TROMINOS
#		remove_child(active_object)
#
#	active_object = Globals.get_object(Globals.SHAPES.TROMINOS, id)
#	active_object.global_position = $centroid.global_position
#
#	add_child(active_object)
	
	# dominos specific
#	if active_object != null:
#		id = (active_object.id + 1) % Globals.N_DOMINOS
#		remove_child(active_object)
#
#	active_object = Globals.get_object(Globals.SHAPES.DOMINOS, id)
#	active_object.global_position = $centroid.global_position
#
#	add_child(active_object)
	
	# monominos specific
#	if active_object != null:
#		id = (active_object.id + 1) % Globals.N_MONOMINOS
#		remove_child(active_object)
#
#	active_object = Globals.get_object(Globals.SHAPES.MONOMINOS, id)
#	active_object.global_position = $centroid.global_position
#
#	add_child(active_object)
	
func execute_translation(action):
	if active_object == null:
		return
		
	match action:	
		'up': active_object.global_position.y -= Globals.LINEAR_DELTA
		'down': active_object.global_position.y += Globals.LINEAR_DELTA
		'left': active_object.global_position.x -= Globals.LINEAR_DELTA
		'right': active_object.global_position.x += Globals.LINEAR_DELTA

		# default case: unrecognized translation
		_: print('unrecogized translation: ', action)

func execute_rotation(action):
	if active_object == null:
		return
		
	match action:
		'rotate_clockwise': active_object.rotation_degrees += Globals.ANGULAR_DELTA
		'rotate_counterclockwise': active_object.rotation_degrees -= Globals.ANGULAR_DELTA
		
		# default case: unrecognized rotation
		_: print('unrecogized rotation: ', action)


func execute_zoom(action):
	if active_object == null:
		return
	
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

func get_screenshot():
	var screenshot = get_viewport().get_texture().get_data()

	# the viewport data is vertically flipped. this is a workaround.
	screenshot.flip_y()
	
	# single value per pixel representing luminance (8-bit depth)
	screenshot.convert(Image.FORMAT_L8)
	
	return screenshot.get_data()

func publish_state():
	var topic = '/polyomino-world/state'

	var shape = null if (active_object == null) else active_object.shape
	var id = null if (active_object == null) else active_object.id
	
	# Godot-AI-Bridge wraps this state into the "data" element of a JSON-encoded message. messages are also
	# given a "header" element containing a unique sequence numbers (seqno) and timestamp in milliseconds
	var msg = {'shape' : shape,
			   'id' : id,
			   'screenshot' : get_screenshot()}

	# broadcasts the message to all clients
	gab.send(topic, msg)
	
	# TODO: Does this variable need to be synchronized???
	unpublished_change = false

#######################
### SIGNAL HANDLERS ###
#######################

# signal handler for publish_timer's "timeout" signal
func _on_publish_state():
	publish_state()


# signal handler for Godot-AI-Bridge's "event_requested" signal
func _on_event_requested(event_details):
	if Globals.DEBUG_MODE:
		print('Godot Environment: event request received -> "%s"' % event_details)
	
	var event = event_details['data']['event']
	if event['type'] == 'action':
		add_action(event['value'])


# signal handler for boundary collisions
func _on_boundary_entered(_area):
	if Globals.DEBUG_MODE:
		print('boundary entered')
		
	boundary_collisions += 1

func _on_boundary_exited(_area):
	if Globals.DEBUG_MODE:
		print('boundary exited')
		
	boundary_collisions -= 1

