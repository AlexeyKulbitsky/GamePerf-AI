# Frame hitch diagnosis

Hitch at frame 150: peak 30.7 ms (1.8x the 16.7 ms budget; median frame 0.0 ms).

## Hypotheses (verify, do not trust)

### 1. A large number of bricks are instantiated in a single frame. — confidence 90%
- pattern: `spawn-burst`
- evidence: `Bricks.instantiate`
- confirm: Count the instances created during the hitch frame and compare with neighboring frames to confirm if this is indeed a spawn burst.
- fix: Pool and reuse bricks instead of creating them on the fly.

### 2. The Physics system may have processed an unusually large batch of active bodies or contacts in one step, overrunning the frame budget. — confidence 60%
- pattern: `physics-burst`
- evidence: `Physics`
- confirm: Compare the active rigid-body and contact count in the hitch frame against neighboring frames to check for a burst of newly woken or spawned bodies.
- fix: Cap or stagger the number of bodies activated per frame.

## Evidence (top offenders by self-time regression)

| span | self-time (µs) | baseline (µs) | regression (µs) |
|---|---:|---:|---:|
| `Bricks.instantiate` | 30657 | 0 | 30657 |
| `Physics` | 4 | 5 | -1 |
