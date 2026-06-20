import importlib


def test_stages_import():
    for stage in ("ingest", "detect", "analyze", "retrieve", "reason"):
        importlib.import_module(f"pipeline.{stage}")
