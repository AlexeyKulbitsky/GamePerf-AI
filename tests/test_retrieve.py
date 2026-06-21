import pytest

from pipeline.ingest import load_trace
from pipeline.detect import find_hitches
from pipeline.analyze import build_evidence
from pipeline.retrieve import retrieve, load_kb

FIXTURES = ["gc-spike", "physics-burst", "sync-asset-load", "n2-collision", "spawn-burst"]


def _bundle(scenario):
    t = load_trace(f"fixtures/synthetic/{scenario}.json")
    return build_evidence(t, find_hitches(t)[0])


def test_kb_has_ten_entries():
    assert len(load_kb()) == 10


@pytest.mark.parametrize("scenario", FIXTURES)
def test_top_match_is_the_planted_cause(scenario):
    results = retrieve(_bundle(scenario))
    assert results[0][0]["id"] == scenario


def test_returns_at_most_top_k_descending():
    results = retrieve(_bundle("gc-spike"))
    assert len(results) <= 3
    scores = [s for _, s in results]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] > 0
