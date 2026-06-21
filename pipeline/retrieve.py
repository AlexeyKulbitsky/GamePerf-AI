"""Match an evidence bundle against the KB entries in kb/.

Keyword/BM25 over the symptoms field for now, embeddings later.
Returns (entry, score) pairs, best first.
"""
import glob
import json
import math
import os
import re
from collections import Counter

K1 = 1.5
B = 0.75
TOP_K = 3
_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text):
    return _TOKEN.findall(text.lower())


def load_kb(kb_dir="kb"):
    entries = []
    for path in sorted(glob.glob(os.path.join(kb_dir, "*.json"))):
        with open(path, encoding="utf-8") as f:
            entries.append(json.load(f))
    return entries


def _doc_tokens(entry):
    text = " ".join([entry["title"], " ".join(entry["symptoms"]), entry["mechanism"]])
    return _tokens(text)


def _query_weights(bundle):
    """token -> weight, weighted by each offender's regression so the dominant
    offender drives retrieval and near-baseline background spans barely count."""
    weights = {}
    for off in bundle["offenders"]:
        w = max(off["regression_us"], 1)
        for tok in _tokens(off["span"]):
            weights[tok] = weights.get(tok, 0) + w
    return weights


def retrieve(bundle, kb_dir="kb", top_k=TOP_K, k1=K1, b=B):
    """Return the top_k (entry, score) KB matches for an evidence bundle."""
    entries = load_kb(kb_dir)
    if not entries:
        return []

    docs = [_doc_tokens(e) for e in entries]
    n = len(docs)
    avgdl = sum(len(d) for d in docs) / n
    df = Counter()
    for d in docs:
        df.update(set(d))

    qweights = _query_weights(bundle)
    scored = []
    for entry, d in zip(entries, docs):
        tf = Counter(d)
        dl = len(d)
        score = 0.0
        for tok, qw in qweights.items():
            f = tf.get(tok, 0)
            if not f:
                continue
            idf = math.log(1 + (n - df[tok] + 0.5) / (df[tok] + 0.5))
            score += qw * idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avgdl))
        scored.append((entry, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
