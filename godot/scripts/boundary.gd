extends Area2D

signal boundary_entered(area)
signal boundary_exited(area)


func _on_area_entered(area):
	emit_signal("boundary_entered", area)


func _on_area_exited(area):
	emit_signal("boundary_exited", area)
