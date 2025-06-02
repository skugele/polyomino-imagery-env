# GDScript: experiment.gd

extends Node2D


onready var rng = RandomNumberGenerator.new()

###############################
# Environment State Variables #
###############################

# a queue of actions that are pending execution
onready var pending_actions = []
onready var last_action_seqno = -1

# state variable for tracking object-boundary collisions
onready var boundary_collisions = {'top': 0,  'bottom': 0, 'left': 0, 'right': 0}

# the reference object (left viewport)
onready var ref_object = null

# the active object (right viewport)
onready var active_object = null

# stores dictionary elements that identify the shape and id for polyominos. the order of these elements
# determines the order in which they will be presented at runtime
onready var polyomino_configs = []

###############################
# State Publication Variables #
###############################

# timer for state (e.g., screenshot) publication to clients
var publish_timer = Timer.new()

# used to preemptively publish a state change ahead of publish_timer timeout
onready var unpublished_change = true


########################
# Child Node Variables #
########################

onready var left_viewport = $viewport_controller/left_viewport_container/left_viewport
onready var right_viewport = $viewport_controller/right_viewport_container/right_viewport

onready var centroid = $viewport_controller/right_viewport_container/right_viewport/centroid

onready var top_boundary = $viewport_controller/right_viewport_container/right_viewport/boundaries/top
onready var bottom_boundary = $viewport_controller/right_viewport_container/right_viewport/boundaries/bottom
onready var left_boundary = $viewport_controller/right_viewport_container/right_viewport/boundaries/left
onready var right_boundary = $viewport_controller/right_viewport_container/right_viewport/boundaries/right


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
	'verbosity': 3  # supported values (-1=FATAL; 0=ERROR; 1=WARNING; 2=INFO; 3=DEBUG; 4=TRACE)
}


func _ready():
	
	rng.randomize()

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
	
	# configures
	initialize_polyomino_configs()


func initialize_polyomino_configs():
	
	for shape_name in Globals.SHAPES:
		var shape = Globals.SHAPES[shape_name]
		for id in Globals.cardinality(shape):
			var config = {'shape': shape, 'id': id}
			polyomino_configs.append(config)


func _input(event):	
	if event.is_action_pressed("ui_up"):
		last_action_seqno += 1
		add_action('up', last_action_seqno)
	elif event.is_action_pressed("ui_down"):
		last_action_seqno += 1
		add_action('down', last_action_seqno)
	elif event.is_action_pressed("ui_left"):
		last_action_seqno += 1
		add_action('left', last_action_seqno)
	elif event.is_action_pressed("ui_right"):
		last_action_seqno += 1
		add_action('right', last_action_seqno)
	elif event.is_action_pressed("ui_rotate_clockwise"):
		last_action_seqno += 1
		add_action('rotate_clockwise', last_action_seqno)
	elif event.is_action_pressed("ui_rotate_counterclockwise"):
		last_action_seqno += 1
		add_action('rotate_counterclockwise', last_action_seqno)
	elif event.is_action_pressed("ui_zoom_in"):
		last_action_seqno += 1
		add_action('zoom_in', last_action_seqno)
	elif event.is_action_pressed("ui_zoom_out"):
		last_action_seqno += 1		
		add_action('zoom_out', last_action_seqno)
	elif event.is_action_pressed("ui_next_shape"):
		last_action_seqno += 1		
		add_action('next_shape', last_action_seqno)


# removes and executes the oldest pending action from the queue (if one exists)
func _process(_delta):	
	if unpublished_change:
		publish_state()
			
	# take corrective actions if boundary collisions occurred due to previous updates
	if has_collision():
		if Globals.DEBUG_MODE:
			print('handling collisions!')
		
		# calculate a movement direction based on the boundaries with collisions
		var corrective_dir = Vector2(0, 0)

		for boundary in get_colliding_boundaries():
			match boundary:
				'top' : corrective_dir += Vector2(0, 1)
				'bottom' : corrective_dir += Vector2(0, -1)
				'left' : corrective_dir += Vector2(1, 0)
				'right' : corrective_dir += Vector2(-1, 0)
				
				_: print('unknown boundary: ', boundary)
				
		active_object.global_position += corrective_dir
		
	else:
		var pending_action = pending_actions.pop_back()
		if pending_action:
			# activity - stop time-based publication
			if not publish_timer.is_stopped():
				publish_timer.stop()
				
			execute(pending_action['action'])
			last_action_seqno = pending_action['seqno']
			unpublished_change = true
		else:
			# inactivity - begin time-based publication
			if publish_timer.is_stopped():
				publish_timer.start()


func has_collision():
	for value in boundary_collisions.values():
		if value > 0:
			return true
			
	return false


func get_colliding_boundaries():
	var boundaries = []
	for key in boundary_collisions.keys():
		if boundary_collisions[key] > 0:
			boundaries.append(key)
			
	return boundaries


# adds an action to the agent's pending_actions queue for later execution
func add_action(action, seqno):	
	if Globals.DEBUG_MODE:
		print('adding action: ', action)
	
	if len(pending_actions) > Globals.MAX_PENDING_ACTIONS:
		var dropped_actions = pending_actions.pop_back()
		print('Max queue depth reached. Dropping oldest pending action with value %s.' % dropped_actions)
	
	pending_actions.push_front({'seqno': seqno, 'action': action})


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


func get_random_position():
	var step_x = rng.randf()
	var step_y = rng.randf()
	
	# TODO: Need constants for the screen dimensions
	var min_step = 50
	var max_step = 85
	
	var position = Vector2(min_step * step_x + max_step * (1 - step_x),
						   min_step * step_y + max_step * (1 - step_y))
						
	return position
	

func get_random_scale():
	var scale_step = rng.randf()
	return Globals.MIN_SCALE * scale_step + Vector2(1.1, 1.1) * (1 - scale_step)


func get_random_rotation():
	var n_rotations = rng.randi_range(1, int(360.0 / Globals.ANGULAR_DELTA))
	return n_rotations * Globals.ANGULAR_DELTA
	

func randomize_object(obj):
	obj.rotation = get_random_rotation()
	obj.scale = get_random_scale()
	obj.global_position = get_random_position()


func generate_image(config):
	var new_object = Globals.get_object(config['shape'], config['id'])
	new_object.global_position = centroid.global_position
		
	return new_object
	
	
func update_ref_image(new_object):
	# remove last polyomino from scene
	if ref_object != null:
		left_viewport.remove_child(ref_object)
		ref_object = null
	
	left_viewport.add_child(new_object)
	ref_object = new_object
	
	
func update_active_image(new_object):
	# remove last polyomino from scene
	if active_object != null:
		right_viewport.remove_child(active_object)
		active_object = null
			
	right_viewport.add_child(new_object)
	active_object = new_object

	
func get_random_config(with_replacement=true):
	var index = rng.randi_range(0, polyomino_configs.size() - 1)
	var config = null
	if with_replacement:
		config = polyomino_configs[index]
	else:
		config = polyomino_configs.pop_left()
	return config
	
	
func execute_next_shape():
	var same = rng.randi() % 2 == 0

	# retrieve configuration details needed to create next polyomino object
	var ref_config = get_random_config()
	
	var active_config = null
	if same:
		active_config = ref_config
	else:
		active_config = get_random_config()
	
	var new_ref_image = generate_image(ref_config)
	var new_active_image = generate_image(active_config)
		
	update_ref_image(new_ref_image)
	update_active_image(new_active_image)
	
	randomize_object(active_object)
	

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

func get_screenshot(viewport):
	var screenshot = viewport.get_texture().get_data()

	# the viewport data is vertically flipped. this is a workaround.
	screenshot.flip_y()
	
	# single value per pixel representing luminance (8-bit depth)
	screenshot.convert(Image.FORMAT_L8)
	
	var byte_array = screenshot.get_data()
	var pixel_data = []
	for i in byte_array.size():
		pixel_data.append(byte_array[i])
	
	return pixel_data

func get_state_msg_for_viewport(viewport, object):
	var shape = null if (object == null) else object.shape
	var id = null if (object == null) else object.id
	
	var screenshot = get_screenshot(viewport)
	
	return {
		'shape' : shape,
		'id' : id,
		'screenshot' : screenshot
	}
	
func publish_state():
	# TODO: move this into a global variable
	var topic = '/polyomino-world/state'
	var msg = {
		'left_viewport': get_state_msg_for_viewport(left_viewport, ref_object),
		'right_viewport': get_state_msg_for_viewport(right_viewport, active_object),
		'last_action_seqno': self.last_action_seqno
	}
	
	# Godot-AI-Bridge wraps this state into the "data" element of a JSON-encoded message. messages 
	# are also given a "header" element containing a unique sequence numbers (seqno) and timestamp 
	# in milliseconds
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
	var header = event_details['header']
	
	if event['type'] == 'action':
		var seqno = header['seqno']
		var action = event['value']
		
		add_action(action, seqno)


# signal handler for boundary collisions
func _on_boundary_entered(boundary):
	if Globals.DEBUG_MODE:
		print('boundary entered: ', boundary)
	
	if boundary == top_boundary:
		boundary_collisions['top'] += 1
	elif boundary == bottom_boundary:
		boundary_collisions['bottom'] += 1
	elif boundary == left_boundary:
		boundary_collisions['left'] += 1
	elif boundary == right_boundary:
		boundary_collisions['right'] += 1


func _on_boundary_exited(boundary):
	if Globals.DEBUG_MODE:
		print('boundary exited: ', boundary)
		
	if boundary == top_boundary:
		boundary_collisions['top'] -= 1
	elif boundary == bottom_boundary:
		boundary_collisions['bottom'] -= 1
	elif boundary == left_boundary:
		boundary_collisions['left'] -= 1
	elif boundary == right_boundary:
		boundary_collisions['right'] -= 1
