"""Trace in, ranked hitch hypotheses out -- the end-to-end CLI.

    python -m pipeline.run <trace.json> [--k K] [--budget US] [--out report.md] [--no-llm]

--no-llm stops after retrieval and dumps the evidence + KB candidates, so the
pipeline is demoable and testable without a running model.
"""
import argparse
import json

from pipeline.ingest import load_trace
from pipeline.detect import find_hitches
from pipeline.analyze import build_evidence
from pipeline.retrieve import retrieve


def run(trace_path, k=3.0, budget_us=16667, kb_dir="kb", use_llm=True):
    """Run the pipeline on one trace and return a markdown report string."""
    trace = load_trace(trace_path, budget_us=budget_us)
    windows = find_hitches(trace, k=k)
    if not windows:
        return "# Frame hitch diagnosis\n\nNo hitches detected.\n"

    window = max(windows, key=lambda w: w.peak_dur_us)  # the worst one
    bundle = build_evidence(trace, window)
    matches = retrieve(bundle, kb_dir=kb_dir)

    if not use_llm:
        return _render_no_llm(bundle, matches)

    from pipeline.reason import reason, render_markdown
    return render_markdown(bundle, matches, reason(bundle, matches))


def _render_no_llm(bundle, matches):
    payload = {
        "window": bundle["window"],
        "frame_context": bundle["frame_context"],
        "offenders": bundle["offenders"],
        "kb_candidates": [{"id": e["id"], "title": e["title"], "score": round(s, 1)}
                          for e, s in matches],
    }
    return "\n".join([
        "# Frame hitch diagnosis (no-LLM)\n",
        "Pipeline ran ingest -> detect -> analyze -> retrieve; LLM stage skipped.\n",
        "```json", json.dumps(payload, indent=2), "```", "",
    ])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Diagnose CPU frame hitches in a trace.")
    ap.add_argument("trace")
    ap.add_argument("--k", type=float, default=3.0, help="MAD multiplier for the hitch threshold")
    ap.add_argument("--budget", type=int, default=16667, help="frame budget in microseconds")
    ap.add_argument("--kb", default="kb", help="knowledge-base directory")
    ap.add_argument("--out", help="write the report here instead of stdout")
    ap.add_argument("--no-llm", action="store_true", help="skip the model; dump evidence + candidates")
    args = ap.parse_args(argv)

    report = run(args.trace, k=args.k, budget_us=args.budget, kb_dir=args.kb,
                 use_llm=not args.no_llm)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"wrote {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
