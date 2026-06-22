"""Evidence bundle + KB matches -> ranked hypotheses.

Single-shot prompt to a local model via Ollama (qwen2.5:7b-instruct).
Primary output is JSON, hypotheses with refs back to the evidence; the
markdown report is rendered from that. Hypotheses are meant to be
verified, not trusted.
"""
import json
import urllib.error
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct"

SYSTEM = (
    "You are a game performance engineer triaging a single CPU frame hitch. "
    "You are given measured evidence (the spans whose self-time regressed most "
    "during the hitch) and a shortlist of candidate hitch patterns from a "
    "knowledge base. Produce ranked hypotheses for what caused the hitch.\n"
    "Rules:\n"
    "- Use ONLY span names that appear in the evidence; never invent spans.\n"
    "- Every hypothesis must cite the evidence spans it rests on in evidence_refs.\n"
    "- Prefer the offender with the largest regression unless the evidence says otherwise.\n"
    "- kb_id must be one of the provided candidate ids, or null if none fit.\n"
    "- Hypotheses are to be verified, not trusted: always give how_to_confirm.\n"
    "Respond with JSON only."
)

SCHEMA_HINT = (
    '{"hypotheses": [{"cause": str, "kb_id": str_or_null, "confidence": 0..1, '
    '"evidence_refs": [span names from the evidence], "how_to_confirm": str, '
    '"suggested_fix": str}]}'
)


def build_prompt(bundle, kb_matches):
    """The user message: the evidence bundle plus the KB shortlist."""
    candidates = [
        {"id": e["id"], "title": e["title"], "mechanism": e["mechanism"],
         "diagnosis_hints": e["diagnosis_hints"], "typical_fixes": e["typical_fixes"]}
        for e, _ in kb_matches
    ]
    return (
        "EVIDENCE (one hitch window):\n" + json.dumps(bundle, indent=2)
        + "\n\nCANDIDATE PATTERNS (from the KB, best match first):\n"
        + json.dumps(candidates, indent=2)
        + "\n\nReturn JSON shaped like: " + SCHEMA_HINT
    )


def _call_ollama(system, user, model=MODEL, url=OLLAMA_URL, timeout=120):
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError) as e:
        raise RuntimeError(
            f"Could not reach Ollama at {url} ({e}). Is the Ollama server running "
            f"and is {model} pulled (`ollama pull {model}`)? "
            f"Run the pipeline with --no-llm to skip the model."
        ) from e
    return body["message"]["content"]


def reason(bundle, kb_matches, model=MODEL, url=OLLAMA_URL):
    """Call the LLM and return the parsed hypotheses dict."""
    content = _call_ollama(SYSTEM, build_prompt(bundle, kb_matches), model=model, url=url)
    return json.loads(content)


def render_markdown(bundle, kb_matches, hypotheses):
    """Render a human-facing report from the hypotheses and the evidence."""
    w, ctx = bundle["window"], bundle["frame_context"]
    span = ("frame %d" % w["first_frame"] if w["last_frame"] == w["first_frame"]
            else "frames %d-%d" % (w["first_frame"], w["last_frame"]))
    lines = [
        "# Frame hitch diagnosis\n",
        f"Hitch at {span}: peak {w['peak_us'] / 1000:.1f} ms "
        f"({w['severity']:.1f}x the {ctx['budget_us'] / 1000:.1f} ms budget; "
        f"median frame {ctx['median_us'] / 1000:.1f} ms).\n",
        "## Hypotheses (verify, do not trust)\n",
    ]
    for i, h in enumerate(hypotheses.get("hypotheses", []), 1):
        conf = h.get("confidence")
        conf_s = f"{conf:.0%}" if isinstance(conf, (int, float)) else "n/a"
        lines.append(f"### {i}. {h.get('cause', '(unnamed)')} — confidence {conf_s}")
        if h.get("kb_id"):
            lines.append(f"- pattern: `{h['kb_id']}`")
        refs = h.get("evidence_refs") or []
        if refs:
            lines.append("- evidence: " + ", ".join("`" + str(r) + "`" for r in refs))
        if h.get("how_to_confirm"):
            lines.append(f"- confirm: {h['how_to_confirm']}")
        if h.get("suggested_fix"):
            lines.append(f"- fix: {h['suggested_fix']}")
        lines.append("")

    lines.append("## Evidence (top offenders by self-time regression)\n")
    lines.append("| span | self-time (µs) | baseline (µs) | regression (µs) |")
    lines.append("|---|---:|---:|---:|")
    for o in bundle["offenders"]:
        lines.append(
            f"| `{o['span']}` | {o['self_time_us']} | {o['baseline_us']} | {o['regression_us']} |"
        )
    lines.append("")
    return "\n".join(lines)
