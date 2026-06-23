import pytest

from pipeline.ingest import load_trace
from pipeline.detect import find_hitches
from pipeline.analyze import build_evidence


def _embed_available():
    try:
        from pipeline.retrieve_embed import _embed
        _embed("search_query: ping")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _embed_available(), reason="nomic-embed-text / Ollama not reachable"
)


def _bundle(path):
    t = load_trace(path)
    return build_evidence(t, max(find_hitches(t), key=lambda w: w.peak_dur_us))


def test_embed_retrieves_planted_cause():
    from pipeline.retrieve_embed import retrieve_embed
    assert retrieve_embed(_bundle("fixtures/synthetic/spawn-burst.json"))[0][0]["id"] == "spawn-burst"


def test_embed_bridges_a_lexical_gap_where_bm25_fails():
    from pipeline.retrieve import retrieve
    from pipeline.retrieve_embed import retrieve_embed
    b = _bundle("fixtures/lexgap/lexgap-spawn.json")  # span "WaveSpawner.deploy"
    assert retrieve(b)[0][0]["id"] != "spawn-burst"        # keyword retrieval misses the synonym
    assert retrieve_embed(b)[0][0]["id"] == "spawn-burst"  # semantic retrieval recovers it
