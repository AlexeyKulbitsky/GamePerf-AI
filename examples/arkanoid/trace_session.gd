extends Node
## Capture harness for the Arkanoid sample. Installed as the autoload
## "TraceSession", it is INERT during normal play and only does anything when
## the game is launched with the user flag `--trace-capture`:
##
##   godot --headless --path examples/arkanoid -- --trace-capture \
##       --out C:/abs/path/arkanoid-capture.json --frames 240 --hitch 150 --hitch-us 30000
##
## While capturing it: (1) turns ChromeTracer on, (2) brackets every physics
## frame, (3) drives the paddle/ball with a tiny autopilot through the real
## input actions so the baseline frames contain real gameplay physics, and
## (4) at frame `--hitch` plays a "spawn wave" -- it instantiates brick.tscn in
## a loop until the frame's work crosses `--hitch-us`. That wave is REAL
## instantiation cost (the engine's spawn-burst bottleneck), just dialled up so
## the spike clears the 16.7 ms budget floor and is reproducible on any machine.
## Nothing is faked: no synthetic GC span, no hand-authored timing.

const LAUNCH_FRAME := 5

var _active := false
var _frame := 0
var _total_frames := 240
var _hitch_frame := 150
var _hitch_us := 30000
var _out_path := "user://arkanoid-capture.json"

var _brick_scene: PackedScene = preload("res://brick.tscn")
var _paddle: Node2D = null
var _closer: Node = null


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if not args.has("--trace-capture"):
		return  # normal play: stay completely out of the way
	_active = true
	for i in args.size():
		if args[i] == "--out" and i + 1 < args.size():
			_out_path = args[i + 1]
		elif args[i] == "--frames" and i + 1 < args.size():
			_total_frames = int(args[i + 1])
		elif args[i] == "--hitch" and i + 1 < args.size():
			_hitch_frame = int(args[i + 1])
		elif args[i] == "--hitch-us" and i + 1 < args.size():
			_hitch_us = int(args[i + 1])

	ChromeTracer.enabled = true
	# Run before every gameplay node so frame_begin opens the frame first...
	process_physics_priority = -1000
	# ...and a sibling that runs after every gameplay node closes it last.
	_closer = FrameCloser.new()
	_closer.session = self
	_closer.process_physics_priority = 1000
	add_child(_closer)


func _physics_process(_delta: float) -> void:
	if not _active:
		return
	ChromeTracer.frame_begin()
	_autopilot()
	if _frame == _hitch_frame:
		_spawn_wave()


func _autopilot() -> void:
	# Launch once, then keep the paddle under the lowest ball -- all through the
	# game's real input actions, so paddle/ball physics run for real every frame.
	if _frame == LAUNCH_FRAME:
		Input.action_press("launch")
	elif _frame == LAUNCH_FRAME + 1:
		Input.action_release("launch")

	if _paddle == null:
		_paddle = get_tree().get_first_node_in_group("paddle") as Node2D
	var ball := _lowest_ball()
	Input.action_release("move_left")
	Input.action_release("move_right")
	if _paddle != null and ball != null:
		if ball.global_position.x < _paddle.global_position.x - 4.0:
			Input.action_press("move_left")
		elif ball.global_position.x > _paddle.global_position.x + 4.0:
			Input.action_press("move_right")


func _lowest_ball() -> Node2D:
	var scene := get_tree().current_scene
	if scene == null:
		return null
	var lowest: Node2D = null
	for child in scene.get_children():
		if child is Ball:
			if lowest == null or (child as Node2D).global_position.y > lowest.global_position.y:
				lowest = child as Node2D
	return lowest


func _spawn_wave() -> void:
	# Real spawn-burst, amplified: instantiate brick.tscn in batches until this
	# frame's instantiation work passes the target, then free them. Construction
	# and scene insertion all land in one frame -- exactly the spawn-burst KB case.
	ChromeTracer.begin("Bricks.instantiate")
	var deadline := Time.get_ticks_usec() + _hitch_us
	while Time.get_ticks_usec() < deadline:
		var holder := Node2D.new()
		add_child(holder)
		for _i in 50:
			holder.add_child(_brick_scene.instantiate())
		holder.free()
	ChromeTracer.end()


func _close_frame() -> void:
	ChromeTracer.frame_end()
	_frame += 1
	if _frame >= _total_frames:
		ChromeTracer.flush(_out_path)
		print("wrote %s (%d frames, spawn wave at %d, ~%d us)"
			% [_out_path, _total_frames, _hitch_frame, _hitch_us])
		get_tree().quit()


## Highest-priority sibling: its _physics_process runs after all gameplay nodes,
## so it closes the frame span around the full frame of work.
class FrameCloser extends Node:
	var session: Node

	func _physics_process(_delta: float) -> void:
		if session != null:
			session._close_frame()
