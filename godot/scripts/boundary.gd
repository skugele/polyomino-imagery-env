extends Area2D

signal boundary_entered(boundary)
signal boundary_exited(boundary)


func _on_area_entered(_area):
	emit_signal("boundary_entered", self)


func _on_area_exited(_area):
	emit_signal("boundary_exited", self)
