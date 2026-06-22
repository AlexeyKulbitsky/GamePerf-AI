class_name Game
extends Node2D

# Controller for a full game session. Owns score / lives / game-state and the set
# of active balls, builds the brick grid from data, spawns power-ups from brick
# drops, applies their effects (delegating the actual changes to paddle/ball), and
# manages the effect timers. Subordinate nodes report up via signals; this script
# commands them via method calls.

const BRICK_SCENE: PackedScene = preload("res://brick.tscn")
const BALL_SCENE: PackedScene = preload("res://ball.tscn")
const POWERUP_SCENE: PackedScene = preload("res://powerup.tscn")

## Brick rectangle size in pixels. Matches the shape in brick.tscn.
const BRICK_SIZE: Vector2 = Vector2(44, 20)
## Gap between adjacent bricks in pixels.
const BRICK_GAP: float = 4.0
## Y position of the top edge of the first brick row.
const GRID_TOP: float = 64.0
## Lives the player starts each session with.
const STARTING_LIVES: int = 3
## How long the wide-paddle and slow-ball effects last, in seconds.
const EFFECT_DURATION: float = 10.0
## Angular spread of the two extra balls spawned by multi-ball.
const MULTI_BALL_SPREAD: float = 0.4363  # ~25 degrees in radians

# Layout codes: 0 = empty, 1 = normal, 2 = tough, 3 = unbreakable.
# Edit this grid to change the level — positions are derived, not hand-placed.
const LAYOUT: Array = [
	[3, 1, 1, 1, 1, 1, 1, 1, 3],
	[1, 2, 1, 2, 1, 2, 1, 2, 1],
	[2, 2, 2, 2, 2, 2, 2, 2, 2],
	[1, 1, 1, 0, 0, 0, 1, 1, 1],
	[3, 0, 1, 0, 3, 0, 1, 0, 3],
]

enum State { PLAYING, WON, LOST }

var _score: int = 0
var _lives: int = STARTING_LIVES
var _breakable_remaining: int = 0
var _state: State = State.PLAYING
var _balls: Array[Ball] = []
var _slow_active: bool = false

@onready var _paddle: Paddle = $Paddle
@onready var _hud: Hud = $HUD
@onready var _wide_timer: Timer = $WidePaddleTimer
@onready var _slow_timer: Timer = $SlowBallTimer


func _ready() -> void:
	_wide_timer.timeout.connect(_on_wide_paddle_timeout)
	_slow_timer.timeout.connect(_on_slow_ball_timeout)
	_start_new_game()


func _unhandled_input(event: InputEvent) -> void:
	# Restart is only available once the round is over.
	if _state == State.PLAYING:
		return
	if event.is_action_pressed("restart"):
		_start_new_game()


func _start_new_game() -> void:
	_clear_bricks()
	_clear_powerups()
	_clear_balls()
	_reset_effects()
	_score = 0
	_lives = STARTING_LIVES
	_state = State.PLAYING
	_build_brick_grid()
	_spawn_ball_on_paddle()
	_hud.set_score(_score)
	_hud.set_lives(_lives)
	_hud.hide_message()


# --- brick grid ----------------------------------------------------------

func _build_brick_grid() -> void:
	_breakable_remaining = 0
	var columns: int = (LAYOUT[0] as Array).size()
	var grid_width: float = columns * BRICK_SIZE.x + (columns - 1) * BRICK_GAP
	var screen_width: float = ProjectSettings.get_setting("display/window/size/viewport_width")
	var left: float = (screen_width - grid_width) * 0.5
	ChromeTracer.begin("Bricks.instantiate")
	for row in range(LAYOUT.size()):
		var row_data: Array = LAYOUT[row]
		for col in range(row_data.size()):
			var code: int = int(row_data[col])
			if code == 0:
				continue
			var brick := BRICK_SCENE.instantiate() as Brick
			brick.brick_type = _code_to_type(code)
			brick.position = Vector2(
				left + col * (BRICK_SIZE.x + BRICK_GAP) + BRICK_SIZE.x * 0.5,
				GRID_TOP + row * (BRICK_SIZE.y + BRICK_GAP) + BRICK_SIZE.y * 0.5
			)
			brick.destroyed.connect(_on_brick_destroyed)
			brick.dropped.connect(_on_brick_dropped)
			if brick.brick_type != Brick.BrickType.UNBREAKABLE:
				_breakable_remaining += 1
			add_child(brick)
	ChromeTracer.end()


func _clear_bricks() -> void:
	for child in get_children():
		if child is Brick:
			child.queue_free()


func _code_to_type(code: int) -> Brick.BrickType:
	match code:
		2:
			return Brick.BrickType.TOUGH
		3:
			return Brick.BrickType.UNBREAKABLE
		_:
			return Brick.BrickType.NORMAL


# --- balls ---------------------------------------------------------------

func _spawn_ball() -> Ball:
	var ball := BALL_SCENE.instantiate() as Ball
	add_child(ball)
	_balls.append(ball)
	if _slow_active:
		ball.set_slow(true)
	return ball


func _spawn_ball_on_paddle() -> void:
	var ball := _spawn_ball()
	ball.reset()


func _clear_balls() -> void:
	for ball in _balls:
		ball.queue_free()
	_balls.clear()


# --- bricks: scoring, drops, win ----------------------------------------

func _on_brick_destroyed(points: int) -> void:
	_score += points
	_hud.set_score(_score)
	_breakable_remaining -= 1
	if _breakable_remaining <= 0 and _state == State.PLAYING:
		_enter_win()


func _on_brick_dropped(at_position: Vector2) -> void:
	var powerup := POWERUP_SCENE.instantiate() as Powerup
	powerup.powerup_type = _random_powerup_type()
	powerup.collected.connect(_on_powerup_collected)
	add_child(powerup)
	powerup.global_position = at_position


func _random_powerup_type() -> Powerup.PowerupType:
	match randi() % 3:
		0:
			return Powerup.PowerupType.WIDE_PADDLE
		1:
			return Powerup.PowerupType.SLOW_BALL
		_:
			return Powerup.PowerupType.MULTI_BALL


func _clear_powerups() -> void:
	for child in get_children():
		if child is Powerup:
			child.queue_free()


# --- power-up effects ----------------------------------------------------

func _on_powerup_collected(powerup_type: Powerup.PowerupType) -> void:
	match powerup_type:
		Powerup.PowerupType.WIDE_PADDLE:
			_paddle.set_wide(true)
			_wide_timer.start(EFFECT_DURATION)  # start() restarts a running timer
		Powerup.PowerupType.SLOW_BALL:
			_slow_active = true
			for ball in _balls:
				ball.set_slow(true)
			_slow_timer.start(EFFECT_DURATION)
		Powerup.PowerupType.MULTI_BALL:
			_spawn_extra_balls()


func _on_wide_paddle_timeout() -> void:
	_paddle.set_wide(false)


func _on_slow_ball_timeout() -> void:
	_slow_active = false
	for ball in _balls:
		ball.set_slow(false)


func _spawn_extra_balls() -> void:
	if _balls.is_empty():
		return
	var source: Ball = _balls[0]
	var pos: Vector2 = source.global_position
	var base_dir: Vector2 = source.velocity if source.velocity.length() > 0.0 else Vector2.UP
	ChromeTracer.begin("Balls.instantiate")
	for angle: float in [-MULTI_BALL_SPREAD, MULTI_BALL_SPREAD]:
		var extra := _spawn_ball()
		extra.global_position = pos
		extra.launch_with_velocity(base_dir.rotated(angle))
	ChromeTracer.end()


func _reset_effects() -> void:
	_wide_timer.stop()
	_slow_timer.stop()
	_slow_active = false
	_paddle.set_wide(false)
	for ball in _balls:
		ball.set_slow(false)


# --- lives / death zone --------------------------------------------------

func _on_death_zone_body_entered(body: Node2D) -> void:
	if _state != State.PLAYING or not (body is Ball):
		return
	var ball := body as Ball
	if not _balls.has(ball):
		return
	_balls.erase(ball)
	ball.queue_free()
	# A life is only lost when the very last ball in play falls.
	if _balls.is_empty():
		_lose_life()


func _lose_life() -> void:
	_lives -= 1
	_hud.set_lives(_lives)
	_reset_effects()
	if _lives <= 0:
		_enter_loss()
	else:
		_spawn_ball_on_paddle()


# --- end states ----------------------------------------------------------

func _enter_win() -> void:
	_state = State.WON
	for ball in _balls:
		ball.freeze()
	_hud.show_message("YOU WIN!\n\nFinal score: %d\n\nPress Enter or R to play again" % _score)


func _enter_loss() -> void:
	_state = State.LOST
	_hud.show_message("GAME OVER\n\nFinal score: %d\n\nPress Enter or R to play again" % _score)
