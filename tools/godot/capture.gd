extends Node
## Headless capture harness. Runs a representative per-frame workload through
## ChromeTracer for N frames, plants one GC.Collect hitch at a known frame, then
## writes the trace and quits. This produces a *real* Godot-engine trace (real
## Time.get_ticks_usec timing, real scheduler jitter), not hand-authored JSON.
##
##   godot --headless --path tools/godot -- --out C:/path/trace.json [--frames 200] [--hitch 120]

var _tracer: Node
var _frame := 0
var _total_frames := 200
var _hitch_frame := 120
var _out_path := "user://trace.json"


func _ready() -> void:
	_tracer = preload("res://chrome_tracer.gd").new()
	add_child(_tracer)

	var args := OS.get_cmdline_user_args()
	for i in args.size():
		if args[i] == "--out" and i + 1 < args.size():
			_out_path = args[i + 1]
		elif args[i] == "--frames" and i + 1 < args.size():
			_total_frames = int(args[i + 1])
		elif args[i] == "--hitch" and i + 1 < args.size():
			_hitch_frame = int(args[i + 1])


func _process(_delta: float) -> void:
	_tracer.frame_begin()

	_tracer.begin("Update"); _spin_us(3000); _tracer.end()
	_tracer.begin("Physics"); _spin_us(4000); _tracer.end()

	_tracer.begin("Render")
	_tracer.begin("DrawCalls"); _spin_us(5000); _tracer.end()
	_spin_us(2000)
	_tracer.end()

	if _frame == _hitch_frame:
		# the planted hitch: a stop-the-world-style pause named to match the KB
		_tracer.begin("GC.Collect"); _spin_us(25000); _tracer.end()

	_tracer.frame_end()

	_frame += 1
	if _frame >= _total_frames:
		_tracer.flush(_out_path)
		print("wrote %s (%d frames, hitch at %d)" % [_out_path, _total_frames, _hitch_frame])
		get_tree().quit()


func _spin_us(us: int) -> void:
	# Busy-wait so the span has real measured duration (engine timing, not a sleep).
	var deadline := Time.get_ticks_usec() + us
	while Time.get_ticks_usec() < deadline:
		pass
