"""Evaluate the pipeline against ground-truth fixtures.

For every trace with a sibling ``<trace>.truth.json``, run the pipeline and score:

- detection recall   -- a hitch window covers the labelled frame (deterministic)
- retrieval rank-1   -- the BM25 top match equals the labelled cause (deterministic)
- LLM top-1 / top-3  -- the labelled cause appears in the top-1 / top-3 hypotheses

Detection and retrieval need no model; the top-k columns call the LLM (skip them
with --no-llm). Writes a markdown table and a CSV for the report.

    python tools/eval.py [--no-llm] [--kb kb]
        [--out-md examples/eval-results.md] [--out-csv examples/eval-results.csv]
"""
import argparse
import csv
import glob
import json
import os

from pipeline.ingest import load_trace
from pipeline.detect import find_hitches
from pipeline.analyze import build_evidence
from pipeline.retrieve import retrieve

ROOTS = ("fixtures/synthetic", "fixtures/real")


def _truth_path(trace_path):
    base = trace_path[:-5] if trace_path.endswith(".json") else trace_path
    return base + ".truth.json"


def discover_cases(roots=ROOTS):
    """Every trace that has a ground-truth sidecar, labelled synthetic/real."""
    cases = []
    for root in roots:
        kind = "real" if "real" in root else "synthetic"
        for trace in sorted(glob.glob(os.path.join(root, "*.json"))):
            if trace.endswith(".truth.json") or not os.path.exists(_truth_path(trace)):
                continue
            with open(_truth_path(trace), encoding="utf-8") as f:
                truth = json.load(f)
            cases.append({"name": os.path.splitext(os.path.basename(trace))[0],
                          "trace": trace, "truth": truth, "kind": kind})
    return cases


def evaluate_case(case, kb_dir="kb", use_llm=True):
    trace = load_trace(case["trace"])
    truth = case["truth"]
    windows = find_hitches(trace)
    row = {"name": case["name"], "kind": case["kind"], "cause": truth["cause_kb_id"],
           "detected": any(w.first_frame <= truth["hitch_frame"] <= w.last_frame for w in windows),
           "retrieval_top1": None, "llm_top1": None, "llm_top3": None, "top_hypothesis": None}
    if not windows:
        return row

    window = max(windows, key=lambda w: w.peak_dur_us)
    bundle = build_evidence(trace, window)
    matches = retrieve(bundle, kb_dir=kb_dir)
    row["retrieval_top1"] = bool(matches) and matches[0][0]["id"] == truth["cause_kb_id"]

    if use_llm:
        from pipeline.reason import reason
        hyps = reason(bundle, matches).get("hypotheses", [])
        kb_ids = [h.get("kb_id") for h in hyps]
        row["llm_top1"] = truth["cause_kb_id"] in kb_ids[:1]
        row["llm_top3"] = truth["cause_kb_id"] in kb_ids[:3]
        if hyps:
            row["top_hypothesis"] = hyps[0].get("kb_id") or hyps[0].get("cause")
    return row


def run_eval(kb_dir="kb", use_llm=True):
    return [evaluate_case(c, kb_dir=kb_dir, use_llm=use_llm) for c in discover_cases()]


def _rate(rows, key):
    vals = [r[key] for r in rows if r[key] is not None]
    return (sum(1 for v in vals if v) / len(vals)) if vals else None


def _fmt(v):
    if v is None:
        return "-"
    if isinstance(v, bool):
        return "yes" if v else "**NO**"
    return str(v)


def to_markdown(rows):
    n = len(rows)
    lines = [
        "# Evaluation results\n",
        f"{n} labelled cases. Detection and retrieval are deterministic; "
        "LLM top-k is at temperature 0.\n",
        "| case | kind | cause | detected | retrieval@1 | llm@1 | llm@3 | top hypothesis |",
        "|---|---|---|:--:|:--:|:--:|:--:|---|",
    ]
    for r in rows:
        top = f"`{r['top_hypothesis']}`" if r["top_hypothesis"] else "-"
        lines.append(
            f"| {r['name']} | {r['kind']} | `{r['cause']}` | {_fmt(r['detected'])} | "
            f"{_fmt(r['retrieval_top1'])} | {_fmt(r['llm_top1'])} | {_fmt(r['llm_top3'])} | {top} |"
        )

    def pct(x):
        return "-" if x is None else f"{x * 100:.0f}%"

    lines += [
        "",
        "## Aggregate\n",
        f"- detection recall: {pct(_rate(rows, 'detected'))} ({n} cases)",
        f"- retrieval rank-1 accuracy: {pct(_rate(rows, 'retrieval_top1'))}",
        f"- LLM top-1 accuracy: {pct(_rate(rows, 'llm_top1'))}",
        f"- LLM top-3 accuracy: {pct(_rate(rows, 'llm_top3'))}",
        "",
    ]
    return "\n".join(lines)


def to_csv(rows, path):
    cols = ["name", "kind", "cause", "detected", "retrieval_top1",
            "llm_top1", "llm_top3", "top_hypothesis"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(cols)
        for r in rows:
            wr.writerow([r[c] for c in cols])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Evaluate the pipeline against ground-truth fixtures.")
    ap.add_argument("--no-llm", action="store_true", help="detection + retrieval only")
    ap.add_argument("--kb", default="kb")
    ap.add_argument("--out-md", default="examples/eval-results.md")
    ap.add_argument("--out-csv", default="examples/eval-results.csv")
    args = ap.parse_args(argv)

    rows = run_eval(kb_dir=args.kb, use_llm=not args.no_llm)
    md = to_markdown(rows)
    os.makedirs(os.path.dirname(args.out_md) or ".", exist_ok=True)
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(md)
    to_csv(rows, args.out_csv)
    print(md)
    print(f"wrote {args.out_md} and {args.out_csv}")


if __name__ == "__main__":
    main()
