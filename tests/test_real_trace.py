from pipeline.run import run


def test_real_godot_trace_diagnoses_gc_spike():
    # fixtures/real/godot-capture.json was captured by the Godot harness in
    # tools/godot (real engine timing). Offline (--no-llm) so it's deterministic.
    report = run("fixtures/real/godot-capture.json", use_llm=False)
    assert "GC.Collect" in report      # the planted offender survives a real capture
    assert "gc-spike" in report        # and retrieval still maps it to the right pattern
