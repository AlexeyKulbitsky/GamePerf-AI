class_name Brick
extends StaticBody2D

# A single configurable brick. The same scene represents every brick type;
# `brick_type` decides its colour, label, and how it reacts to being hit.

## Emitted when this brick is destroyed, carrying the score it is worth.
signal destroyed(points: int)

## Emitted when this (normal) brick rolls a successful power-up drop.
signal dropped(at_position: Vector2)

enum BrickType { NORMAL, TOUGH, UNBREAKABLE }

## Which kind of brick this is. Set per-instance by the grid generator in game.gd.
@export var brick_type: BrickType = BrickType.NORMAL

# Score awarded on destruction. Tough bricks are worth more because they take
# two hits to break; unbreakable bricks are never destroyed and award nothing.
const POINTS_NORMAL: int = 100
const POINTS_TOUGH: int = 250

## Chance (0..1) that destroying a normal brick drops a power-up.
const DROP_CHANCE: float = 0.25

# Distinct colour per type so the player can tell them apart at a glance, plus a
# clearly different colour for a tough brick that has already taken one hit.
const COLOR_NORMAL: Color = Color(0.30, 0.75, 0.35)
const COLOR_TOUGH: Color = Color(0.95, 0.60, 0.20)
const COLOR_TOUGH_DAMAGED: Color = Color(0.80, 0.28, 0.16)
const COLOR_UNBREAKABLE: Color = Color(0.55, 0.55, 0.62)

# Tough bricks survive one hit; this flips to true after that first hit.
var _damaged: bool = false

@onready var _rect: ColorRect = $ColorRect


func _ready() -> void:
	_refresh_appearance()


## Processes one ball impact. The ball has already bounced before calling this.
func hit() -> void:
	match brick_type:
		BrickType.NORMAL:
			_maybe_drop_powerup()
			_destroy(POINTS_NORMAL)
		BrickType.TOUGH:
			if _damaged:
				_destroy(POINTS_TOUGH)
			else:
				_damaged = true
				_refresh_appearance()
		BrickType.UNBREAKABLE:
			pass


func _destroy(points: int) -> void:
	destroyed.emit(points)
	queue_free()


# Only normal bricks reach this; tough and unbreakable never drop power-ups.
func _maybe_drop_powerup() -> void:
	if randf() < DROP_CHANCE:
		dropped.emit(global_position)


func _refresh_appearance() -> void:
	match brick_type:
		BrickType.NORMAL:
			_rect.color = COLOR_NORMAL
		BrickType.TOUGH:
			_rect.color = COLOR_TOUGH_DAMAGED if _damaged else COLOR_TOUGH
		BrickType.UNBREAKABLE:
			_rect.color = COLOR_UNBREAKABLE
