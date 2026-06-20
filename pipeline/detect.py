"""Find hitch windows in the frame-time series.

First version is statistical: a frame is a candidate when its duration
exceeds median + k*MAD, with the frame budget (16.6 ms at 60 fps) as a
floor. Returns HitchWindow(first_frame, last_frame, peak_duration_us,
severity).

Planned replacement: Chronos-Bolt behind the same interface.
"""
