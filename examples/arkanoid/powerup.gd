class_name Powerup
extends Area2D

# A falling power-up. The same scene represents all three types; `powerup_type`
# decides its colour and label. It only falls and reports being caught — it never
# touches the paddle or ball directly. The Area2D root lets it detect the paddle
# without the ball physically bouncing off it.

## Emitted when the paddle catches this power-up.
signal collected(powerup_type: PowerupType)

enum PowerupType { WIDE_PADDLE, SLOW_BALL, MULTI_BALL }

## Which effect this power-up grants. Set per-drop by the spawner in game.gd.
@export var powerup_type: PowerupType = PowerupType.WIDE_PADDLE

## Constant downward fall speed in pixels per second.
const FALL_SPEED: float = 140.0

const COLOR_WIDE: Color = Color(0.30, 0.55, 0.95)   # blue  - wide paddle
const COLOR_SLOW: Color = Color(0.95, 0.85, 0.20)   # yellow - slow ball
const COLOR_MULTI: Color = Color(0.30, 0.80, 0.40)  # green - multi-ball

var _despawn_y: float = 0.0

@onready var _rect: ColorRect = $ColorRect
@onready var _label: Label = $Label


func _ready() -> void:
	_despawn_y = float(ProjectSettings.get_setting("display/window/size/viewport_height")) + 30.0
	_apply_appearance()
	body_entered.connect(_on_body_entered)


func _physics_process(delta: float) -> void:
	position.y += FALL_SPEED * delta
	if position.y > _despawn_y:
		queue_free()


func _on_body_entered(body: Node2D) -> void:
	if body is Paddle:
		collected.emit(powerup_type)
		queue_free()


func _apply_appearance() -> void:
	match powerup_type:
		PowerupType.WIDE_PADDLE:
			_rect.color = COLOR_WIDE
			_label.text = "W"
		PowerupType.SLOW_BALL:
			_rect.color = COLOR_SLOW
			_label.text = "S"
		PowerupType.MULTI_BALL:
			_rect.color = COLOR_MULTI
			_label.text = "M"
