extends Node
## Drop-in hitch injector for a real game (e.g. Arkanoid).
##
## Requires chrome_tracer.gd registered as an autoload named "ChromeTracer".
## Add this node anywhere in a running scene: every `period` frames it busy-waits
## ~`busy_ms` inside a GC.Collect span, planting a known hitch so the pipeline has
## ground truth to score against. Remove it to capture an un-doctored trace.

@export var period := 90
@export var busy_ms := 25

var _frame := 0


func _process(_delta: float) -> void:
	_frame += 1
	if _frame % period == 0:
		ChromeTracer.begin("GC.Collect")
		var deadline := Time.get_ticks_usec() + busy_ms * 1000
		while Time.get_ticks_usec() < deadline:
			pass
		ChromeTracer.end()
