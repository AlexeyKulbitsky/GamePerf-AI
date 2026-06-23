# Evaluation results

6 labelled cases. Detection and retrieval are deterministic; LLM top-k is at temperature 0.

| case | kind | cause | detected | retrieval@1 | llm@1 | llm@3 | top hypothesis |
|---|---|---|:--:|:--:|:--:|:--:|---|
| gc-spike | synthetic | `gc-spike` | yes | yes | yes | yes | `gc-spike` |
| n2-collision | synthetic | `n2-collision` | yes | yes | yes | yes | `n2-collision` |
| physics-burst | synthetic | `physics-burst` | yes | yes | yes | yes | `physics-burst` |
| spawn-burst | synthetic | `spawn-burst` | yes | yes | yes | yes | `spawn-burst` |
| sync-asset-load | synthetic | `sync-asset-load` | yes | yes | yes | yes | `sync-asset-load` |
| arkanoid-capture | real | `spawn-burst` | yes | yes | yes | yes | `spawn-burst` |

## Aggregate

- detection recall: 100% (6 cases)
- retrieval rank-1 accuracy: 100%
- LLM top-1 accuracy: 100%
- LLM top-3 accuracy: 100%
