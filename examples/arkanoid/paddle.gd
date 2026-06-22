class_name Paddle
extends CharacterBody2D

## Horizontal movement speed in pixels per second. Tunable from the inspector.
@export var speed: float = 480.0

## Thickness of the side walls in pixels, used to keep the paddle inside the
## play area. Matches the wall thickness configured in game.tscn.
@export var wall_thickness: float = 16.0

## Default and widened paddle widths in pixels (wide-paddle power-up).
@export var normal_width: float = 80.0
@export var wide_width: float = 140.0

var _width: float = 0.0
# Pre-computed horizontal clamp limits (paddle origin is its centre).
var _min_x: float = 0.0
var _max_x: float = 0.0


func _ready() -> void:
	_set_width(normal_width)


func _physics_process(delta: float) -> void:
	# get_axis returns -1, 0 or 1 from the move_left / move_right actions.
	# Multiplying by delta keeps the speed identical at any frame rate.
	var direction: float = Input.get_axis("move_left", "move_right")
	position.x += direction * speed * delta
	position.x = clampf(position.x, _min_x, _max_x)


## Switches between the normal and widened paddle size (wide-paddle power-up).
func set_wide(active: bool) -> void:
	_set_width(wide_width if active else normal_width)


## Current half-width, used by the ball to map paddle-relative bounce angles.
func get_half_width() -> float:
	return _width * 0.5


func _set_width(new_width: float) -> void:
	_width = new_width
	# Resize the collision shape and the visual together so they stay in sync.
	(($CollisionShape2D.shape) as RectangleShape2D).size.x = new_width
	$ColorRect.offset_left = -new_width * 0.5
	$ColorRect.offset_right = new_width * 0.5
	# Recompute the clamp limits for the new width and keep the paddle in bounds.
	var half_width: float = new_width * 0.5
	var screen_width: float = ProjectSettings.get_setting("display/window/size/viewport_width")
	_min_x = wall_thickness + half_width
	_max_x = screen_width - wall_thickness - half_width
	position.x = clampf(position.x, _min_x, _max_x)
