"""Parse Chrome Tracing JSON into a frame series + span tree.

Accepts the array form or {"traceEvents": [...]}. Only complete events
("ph": "X", ts/dur in microseconds) are used. Frames are delimited by a
span named "frame" on the main thread.

Gives back frames (index, start_us, duration_us) and per-frame spans
(name, start_us, duration_us, depth).
"""
