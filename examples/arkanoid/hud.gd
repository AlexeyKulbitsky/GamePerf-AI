class_name Hud
extends CanvasLayer

# Pure presentation. The HUD holds no game state — game.gd pushes values in
# through these methods. It never reads the ball, bricks, or game state itself.

@onready var _score_label: Label = $ScoreLabel
@onready var _lives_label: Label = $LivesLabel
@onready var _message_label: Label = $MessageLabel
@onready var _overlay: ColorRect = $Overlay


func set_score(value: int) -> void:
	_score_label.text = "Score: %d" % value


func set_lives(value: int) -> void:
	_lives_label.text = "Lives: %d" % value


## Shows a centred end-of-game message over a dimming overlay.
func show_message(text: String) -> void:
	_message_label.text = text
	_message_label.show()
	_overlay.show()


func hide_message() -> void:
	_message_label.hide()
	_overlay.hide()
