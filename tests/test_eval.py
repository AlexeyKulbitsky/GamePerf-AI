import importlib.util
import os


def _load_eval():
    # tools/ isn't a package; load the script straight from its path.
    spec = importlib.util.spec_from_file_location("gp_eval", os.path.join("tools", "eval.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gp_eval = _load_eval()


def test_discovers_synthetic_real_and_lexgap_cases():
    cases = gp_eval.discover_cases()
    names = {c["name"] for c in cases}
    assert {"gc-spike", "physics-burst", "sync-asset-load",
            "n2-collision", "spawn-burst"} <= names
    assert "arkanoid-capture" in names                       # real instrumented game
    assert {"lexgap-spawn", "lexgap-gc", "lexgap-shader", "lexgap-asset"} <= names
    assert any(c["kind"] == "lexical-gap" for c in cases)


def test_detection_perfect_and_bm25_fails_only_on_lexical_gap_offline():
    rows = gp_eval.run_eval(use_llm=False, use_embed=False)
    assert rows
    assert all(r["detected"] for r in rows)  # every labelled hitch is found
    clean = [r for r in rows if r["kind"] != "lexical-gap"]
    lexgap = [r for r in rows if r["kind"] == "lexical-gap"]
    assert clean and lexgap
    assert all(r["bm25_top1"] for r in clean)           # keyword retrieval nails clean cases
    assert all(r["bm25_top1"] is False for r in lexgap)  # but cannot bridge the lexical gap
    assert all(r["embed_top1"] is None for r in rows)    # embed gated off here


def test_markdown_table_renders():
    md = gp_eval.to_markdown(gp_eval.run_eval(use_llm=False, use_embed=False))
    assert "# Evaluation results" in md
    assert "detection recall: 100%" in md
    assert "bm25@1" in md and "embed@1" in md
