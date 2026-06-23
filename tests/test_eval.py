import importlib.util
import os


def _load_eval():
    # tools/ isn't a package; load the script straight from its path.
    spec = importlib.util.spec_from_file_location("gp_eval", os.path.join("tools", "eval.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gp_eval = _load_eval()


def test_discovers_synthetic_and_real_labelled_cases():
    names = {c["name"] for c in gp_eval.discover_cases()}
    assert {"gc-spike", "physics-burst", "sync-asset-load",
            "n2-collision", "spawn-burst"} <= names
    assert "arkanoid-capture" in names  # the real instrumented-game trace


def test_detection_and_retrieval_are_perfect_offline():
    rows = gp_eval.run_eval(use_llm=False)
    assert rows
    assert all(r["detected"] for r in rows)          # every labelled hitch is found
    assert all(r["retrieval_top1"] for r in rows)    # and mapped to the right pattern
    assert all(r["llm_top1"] is None for r in rows)  # llm columns stay unset offline


def test_markdown_table_renders():
    md = gp_eval.to_markdown(gp_eval.run_eval(use_llm=False))
    assert "# Evaluation results" in md
    assert "detection recall: 100%" in md
