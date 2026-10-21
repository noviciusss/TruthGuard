# Deterministic ablations — frozen TEST split

All three effective variants ran on all 140 frozen TEST questions with no API calls. The JSONL output is resumable stage evidence. The full system uses the same BGE/FAISS retrieval and deterministic critic.

| Variant | n | Answer proxy (95% CI) | Conflict F1 (95% CI) | Mode accuracy (95% CI) | TEST T0 false-conflicts | Public outputs differing from full |
|---|---:|---:|---:|---:|---:|---:|
| full_system | 140 | 0.7000 [0.6214, 0.7714] | 0.8763 [0.8242, 0.9192] | 0.7000 [0.6214, 0.7714] | 0/18 (0.0000) | 0 |
| no_critic | 140 | 0.8929 [0.8429, 0.9429] | 0.0000 [0.0000, 0.0000] | 0.1286 [0.0786, 0.1857] | 0/18 (0.0000) | 140 |
| no_metadata_inference | 140 | 0.7000 [0.6214, 0.7714] | 0.8763 [0.8242, 0.9192] | 0.7000 [0.6214, 0.7714] | 0/18 (0.0000) | 4 |
| no_supersession_graph | 140 | 0.7000 [0.6214, 0.7714] | 0.7471 [0.6667, 0.8172] | 0.5571 [0.4786, 0.6429] | 0/18 (0.0000) | 20 |

## Variant semantics

- `no_critic`: passage-only Naive RAG answer path.
- `no_supersession_graph`: graph construction and graph-neighbor retrieval disabled.
- `no_metadata_inference`: body/filename metadata inference disabled; header metadata only.
- `no_self_critique` and `no_conflict_seeking_expansion` were removed from the reported table because their frozen TEST runs changed no public answer/status/conflict outputs (only retrieval/trace internals). They are not claimed as effective ablations.

The reported full-system baseline is deterministic and offline. These are component ablations, not live-provider results.
