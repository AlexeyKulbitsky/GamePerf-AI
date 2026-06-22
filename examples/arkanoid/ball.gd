class_name Ball
extends CharacterBody2D

## Default travel speed in pixels per second. Tunable from the inspector.
@export var speed: float = 320.0

## Radius of the ball in pixels. Kept in sync with the CircleShape2D in ball.tscn.
@export var radius: float = 8.0

## Fill colour of the ball.
@export var color: Color = Color(0.55, 0.9, 1.0)

# Smallest share of the speed that must stay vertical after any bounce, so the
# ball can never settle into a flat horizontal loop.
const MIN_VERTICAL_RATIO: float = 0.3
# Fraction of the base speed used while the slow-ball power-up is active.
const SLOW_FACTOR: float = 0.55

# Widest deflection from straight-up when the ball hits the far edge of the
# paddle, and the random spread applied to the initial launch.
var _max_paddle_angle: float = deg_to_rad(60.0)
var _launch_spread: float = deg_to_rad(20.0)

var _base_speed: float = 0.0  # Remembers the default so slow-ball can revert.
var _launched: bool = false
var _frozen: bool = false  # When true the ball ignores input and stops moving.
var _paddle: Paddle = null
var _rest_offset: float = 0.0  # Vertical offset above the paddle while resting.


func _ready() -> void:
	_base_speed = speed
	_paddle = get_tree().get_first_node_in_group("paddle") as Paddle
	if _paddle != null:
		var paddle_shape := _paddle.get_node("CollisionShape2D").shape as RectangleShape2D
		_rest_offset = -(paddle_shape.size.y * 0.5 + radius + 1.0)
	reset()


func _draw() -> void:
	draw_circle(Vector2.ZERO, radius, color)


func _physics_process(delta: float) -> void:
	if _frozen:
		return
	if not _launched:
		_rest_on_paddle()
		if Input.is_action_just_pressed("launch"):
			_launch()
		return

	ChromeTracer.begin("Physics")
	var collision := move_and_collide(velocity * delta)
	if collision != null:
		_bounce(collision)
	ChromeTracer.end()


## Returns the ball to its pre-launch state at default speed, resting on the paddle.
func reset() -> void:
	_frozen = false
	_launched = false
	speed = _base_speed
	velocity = Vector2.ZERO
	_rest_on_paddle()


## Stops the ball in place (used when the game is won or lost).
func freeze() -> void:
	_frozen = true
	velocity = Vector2.ZERO


## Applies or clears the slow-ball effect, preserving the current direction.
func set_slow(active: bool) -> void:
	speed = _base_speed * SLOW_FACTOR if active else _base_speed
	if _launched:
		velocity = velocity.normalized() * speed


## Launches an extra (multi-ball) ball in a given direction at the current speed.
func launch_with_velocity(direction: Vector2) -> void:
	_frozen = false
	_launched = true
	velocity = direction.normalized() * speed


func _rest_on_paddle() -> void:
	if _paddle != null:
		global_position = _paddle.global_position + Vector2(0.0, _rest_offset)


func _launch() -> void:
	var angle: float = randf_range(-_launch_spread, _launch_spread)
	velocity = Vector2(sin(angle), -cos(angle)) * speed
	_launched = true


func _bounce(collision: KinematicCollision2D) -> void:
	var collider := collision.get_collider()
	if collider == _paddle:
		# Direction is decided by where the ball met the paddle, not by the
		# incoming angle: left edge -> upper-left, centre -> up, right -> upper-right.
		velocity = _paddle_bounce_velocity()
	else:
		# Walls, ceiling and bricks all reflect the velocity across the normal.
		velocity = velocity.bounce(collision.get_normal())
		if collider is Brick:
			(collider as Brick).hit()
	_enforce_min_vertical()


func _paddle_bounce_velocity() -> Vector2:
	# Use the paddle's current half-width so the mapping stays correct when wide.
	var half_width: float = _paddle.get_half_width()
	var offset: float = (global_position.x - _paddle.global_position.x) / half_width
	offset = clampf(offset, -1.0, 1.0)
	var angle: float = offset * _max_paddle_angle
	return Vector2(sin(angle), -cos(angle)) * speed


func _enforce_min_vertical() -> void:
	# Travel at exactly `speed` first, then, if the trajectory is too flat,
	# rebuild it from a floored vertical component so speed stays constant.
	velocity = velocity.normalized() * speed
	var min_vertical: float = speed * MIN_VERTICAL_RATIO
	if absf(velocity.y) < min_vertical:
		var vertical_sign: float = signf(velocity.y)
		if vertical_sign == 0.0:
			vertical_sign = -1.0  # Default upward if perfectly horizontal.
		var horizontal_sign: float = signf(velocity.x)
		if horizontal_sign == 0.0:
			horizontal_sign = 1.0
		velocity.y = vertical_sign * min_vertical
		velocity.x = horizontal_sign * sqrt(speed * speed - min_vertical * min_vertical)
