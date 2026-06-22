extends Node
## Minimal Chrome Tracing writer for Godot.
##
## Use it as an autoload singleton (Project Settings -> Autoload, name it
## "ChromeTracer") or instance it directly. Wrap work with begin()/end() and
## bracket each frame with frame_begin()/frame_end(); flush() writes the trace
## as Chrome Tracing JSON that GamePerf-AI's ingest stage reads directly.

const PID := 1
const TID := 1  # everything goes on one logical "main thread"

## When false (the default) every call below is a no-op, so the singleton can
## stay installed in a shipping game with zero per-frame cost. The capture
## harness (trace_session.gd) flips this on only while it is recording.
var enabled := false

var _events: Array = []
var _stack: Array = []          # of [name, start_us]
var _frame_open := false
var _frame_start_us := 0


func _now_us() -> int:
	return Time.get_ticks_usec()


func begin(p_name: String) -> void:
	if not enabled:
		return
	_stack.push_back([p_name, _now_us()])


func end() -> void:
	if not enabled or _stack.is_empty():
		return
	var top: Array = _stack.pop_back()
	_emit(top[0], top[1], _now_us() - top[1])


func frame_begin() -> void:
	if not enabled:
		return
	_frame_open = true
	_frame_start_us = _now_us()


func frame_end() -> void:
	if _frame_open:
		_emit("frame", _frame_start_us, _now_us() - _frame_start_us)
		_frame_open = false


func _emit(p_name: String, ts_us: int, dur_us: int) -> void:
	_events.append({
		"name": p_name, "ph": "X", "ts": ts_us, "dur": dur_us,
		"pid": PID, "tid": TID,
	})


func flush(path: String) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		push_error("ChromeTracer: cannot open %s" % path)
		return
	f.store_string(JSON.stringify({"traceEvents": _events, "displayTimeUnit": "ms"}, "  "))
	f.close()
