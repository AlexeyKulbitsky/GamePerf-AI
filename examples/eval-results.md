# Evaluation results

10 labelled cases. Detection and retrieval are deterministic; LLM top-k is at temperature 0. BM25 vs embed = keyword vs semantic KB retrieval (nomic-embed-text).

| case | kind | cause | detected | bm25@1 | embed@1 | llm@1 | llm@3 | top hypothesis |
|---|---|---|:--:|:--:|:--:|:--:|:--:|---|
| gc-spike | synthetic | `gc-spike` | yes | yes | yes | yes | yes | `gc-spike` |
| n2-collision | synthetic | `n2-collision` | yes | yes | yes | yes | yes | `n2-collision` |
| physics-burst | synthetic | `physics-burst` | yes | yes | yes | yes | yes | `physics-burst` |
| spawn-burst | synthetic | `spawn-burst` | yes | yes | yes | yes | yes | `spawn-burst` |
| sync-asset-load | synthetic | `sync-asset-load` | yes | yes | yes | yes | yes | `sync-asset-load` |
| lexgap-asset | lexical-gap | `sync-asset-load` | yes | **NO** | **NO** | **NO** | **NO** | `physics-burst` |
| lexgap-gc | lexical-gap | `gc-spike` | yes | **NO** | yes | **NO** | **NO** | `MemoryReclaimer.sweep took significantly longer than usual` |
| lexgap-shader | lexical-gap | `shader-compile` | yes | **NO** | yes | **NO** | **NO** | `PipelineCache.prime took significantly longer than usual` |
| lexgap-spawn | lexical-gap | `spawn-burst` | yes | **NO** | yes | **NO** | **NO** | `WaveSpawner.deploy is responsible for a significant regression during this frame.` |
| arkanoid-capture | real | `spawn-burst` | yes | yes | yes | yes | yes | `spawn-burst` |

## Aggregate

- detection recall: 100% (10 cases)
- BM25 rank-1: 60% overall | clean 100% | lexical-gap 0%
- embed rank-1: 90% overall | clean 100% | lexical-gap 75%
- LLM top-1: 60% | top-3: 60%
