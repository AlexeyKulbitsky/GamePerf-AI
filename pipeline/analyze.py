"""Turn a hitch window into an evidence bundle.

Self-time per span name across the window vs the same spans in nearby
normal frames, top offenders ranked by regression. Bundle is plain JSON:
window, offenders (span, self_time_us, baseline_us, ratio), frame_context
(median_us, budget_us).
"""
