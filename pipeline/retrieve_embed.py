"""Semantic KB retrieval via a local embedding model (Ollama).

An alternative to retrieve.py's BM25. It embeds each KB entry and a query built
from the evidence with nomic-embed-text, then ranks by cosine similarity. The
point is to catch hitches whose offending span shares no keywords with the KB
but means the same thing (e.g. a span named "WaveSpawner.deploy" -> spawn-burst),
where pure keyword matching falls down.

Same shape as retrieve(): retrieve_embed(bundle, kb_dir) -> [(entry, score)].
"""
import json
import math
import re
import urllib.error
import urllib.request

from pipeline.retrieve import load_kb

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
TOP_K = 3

# nomic-embed-text is trained with task prefixes; using them improves retrieval.
_DOC_PREFIX = "search_document: "
_QUERY_PREFIX = "search_query: "

_doc_cache = {}  # (kb_dir, model) -> (entries, vectors)


def _embed(text, model=EMBED_MODEL, url=OLLAMA_EMBED_URL, timeout=60):
    req = urllib.request.Request(
        url, data=json.dumps({"model": model, "prompt": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError) as e:
        raise RuntimeError(
            f"Could not reach Ollama embeddings at {url} ({e}). "
            f"Is the model pulled (`ollama pull {model}`)?"
        ) from e
    return body["embedding"]


def _doc_text(entry):
    return _DOC_PREFIX + entry["title"] + ". " + ". ".join(entry["symptoms"]) + ". " + entry["mechanism"]


def _words(name):
    """Split a span name (CamelCase / dots / underscores) into lowercase words."""
    return " ".join(re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", name)).lower()


def _query_text(bundle):
    """Query = the words of the spans that actually regressed.

    Just the offender names, no boilerplate: experiments showed generic hitch
    phrasing ("a CPU frame hitch dominated by ...") dilutes the signal and pulls
    the match toward the most common patterns, while the dominant span's own
    words carry the semantics. Background spans (near-zero regression) are
    dropped so they don't mislead the embedding.
    """
    offenders = bundle.get("offenders", [])
    if not offenders:
        return _QUERY_PREFIX + "frame hitch"
    top_reg = max(offenders[0]["regression_us"], 1)
    spans = [o["span"] for o in offenders if o["regression_us"] >= 0.15 * top_reg]
    if not spans:
        spans = [offenders[0]["span"]]
    return _QUERY_PREFIX + " ".join(_words(s) for s in spans)


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _kb_vectors(kb_dir, model):
    key = (kb_dir, model)
    if key not in _doc_cache:
        entries = load_kb(kb_dir)
        _doc_cache[key] = (entries, [_embed(_doc_text(e), model=model) for e in entries])
    return _doc_cache[key]


def retrieve_embed(bundle, kb_dir="kb", top_k=TOP_K, model=EMBED_MODEL):
    """Return the top_k (entry, cosine_score) KB matches for an evidence bundle."""
    entries, vecs = _kb_vectors(kb_dir, model)
    qv = _embed(_query_text(bundle), model=model)
    scored = [(e, _cosine(qv, v)) for e, v in zip(entries, vecs)]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
