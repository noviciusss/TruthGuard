# Deterministic ablations — frozen TEST split

All three effective variants ran on all 146 frozen TEST questions with no API calls. The JSONL output is resumable stage evidence. The full system and all variants use the same HashEmbedder retrieval backend and deterministic critic.

| Variant | n | Answer proxy (95% CI) | Macro answer | Conflict F1 (95% CI) | Macro conflict F1 | Mode accuracy (95% CI) | Macro mode | TEST T0 false-conflicts | Public outputs differing from full |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full_system | 146 | 0.7123 [0.6370, 0.7808] | 0.8068 | 0.8835 [0.8324, 0.9224] | 0.6654 | 0.6781 [0.5890, 0.7534] | 0.7721 | 0/18 (0.0000) | 0 |
| no_critic | 146 | 0.8082 [0.7534, 0.8699] | 0.7032 | 0.0000 [0.0000, 0.0000] | 0.0000 | 0.1233 [0.0753, 0.1781] | 0.1250 | 0/18 (0.0000) | 146 |
| no_metadata_inference | 146 | 0.7123 [0.6370, 0.7808] | 0.8068 | 0.8557 [0.7979, 0.9023] | 0.6546 | 0.6438 [0.5616, 0.7192] | 0.7548 | 0/18 (0.0000) | 10 |
| no_supersession_graph | 146 | 0.7123 [0.6370, 0.7808] | 0.8068 | 0.6782 [0.5904, 0.7553] | 0.4722 | 0.4589 [0.3699, 0.5411] | 0.5719 | 0/18 (0.0000) | 33 |

## Variant semantics

- `no_critic`: passage-only Naive RAG answer path.
- `no_supersession_graph`: graph construction and graph-neighbor retrieval disabled.
- `no_metadata_inference`: body/filename metadata inference disabled; header metadata only.
- `no_self_critique` and `no_conflict_seeking_expansion` were removed from the reported table because their frozen TEST runs changed no public answer/status/conflict outputs (only retrieval/trace internals). They are not claimed as effective ablations.

The reported full-system baseline is deterministic and offline. These are component ablations, not live-provider results.
