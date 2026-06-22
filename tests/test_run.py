from pipeline.run import run, main


def test_no_llm_end_to_end_mentions_offender_and_kb():
    # ingest -> detect -> analyze -> retrieve, no model required.
    report = run("fixtures/synthetic/gc-spike.json", use_llm=False)
    assert "GC.Collect" in report                 # the planted offender span
    assert "Garbage collection spike" in report   # the gc-spike KB title


def test_main_writes_report_to_file(tmp_path):
    out = tmp_path / "report.md"
    main(["fixtures/synthetic/physics-burst.json", "--no-llm", "--out", str(out)])
    text = out.read_text(encoding="utf-8")
    assert "Physics2DServer.flush_queries" in text
    assert "physics-burst" in text


def test_no_hitch_trace_reports_nothing(tmp_path):
    # A flat trace (no spike) should detect no hitches.
    import json
    events = []
    ts = 0
    for i in range(50):
        events.append({"name": "frame", "ph": "X", "ts": ts, "dur": 14000, "pid": 1, "tid": 1})
        ts += 14000
    p = tmp_path / "flat.json"
    p.write_text(json.dumps(events), encoding="utf-8")
    report = run(str(p), use_llm=False)
    assert "No hitches detected" in report
