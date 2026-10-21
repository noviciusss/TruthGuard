# Frozen v2 TEST metrics by type

All values are deterministic/offline results from the frozen 146-question v2 TEST split using HashEmbedder retrieval and the deterministic critic. No provider answered these rows.

Conflict precision/recall/F1 treat each question as conflict-positive for T1–T6 and conflict-negative for T0/T7. Mode accuracy requires the gold final status. T6 abstention is strict `status=abstained`; T7 `not_in_corpus` recall is reported separately.

| Type | n | Conflict P | Conflict R | Conflict F1 | Mode accuracy | T6 abstention precision | T6 abstention recall | Non-T6 false-abstain rate | T0 false-conflict rate | T7 not-in-corpus recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| T0 | 18 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.2069 | 1.0000 | 0.1643 | 0.0000 | — |
| T1 | 17 | 1.0000 | 0.7647 | 0.8667 | 0.7647 | 0.2069 | 1.0000 | 0.1643 | — | — |
| T2 | 18 | 1.0000 | 0.7222 | 0.8387 | 0.7222 | 0.2069 | 1.0000 | 0.1643 | — | — |
| T3 | 36 | 1.0000 | 0.8611 | 0.9254 | 0.2222 | 0.2069 | 1.0000 | 0.1643 | — | — |
| T4 | 17 | 1.0000 | 0.7059 | 0.8276 | 0.7059 | 0.2069 | 1.0000 | 0.1643 | — | — |
| T5 | 21 | 1.0000 | 0.7619 | 0.8649 | 0.7619 | 0.2069 | 1.0000 | 0.1643 | — | — |
| T6 | 6 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.2069 | 1.0000 | 0.1643 | — | — |
| T7 | 13 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.2069 | 1.0000 | 0.1643 | — | 1.0000 |
| **Overall** | **146** | **1.0000** | **0.7913** | **0.8835** | **0.6781** | **0.2069** | **1.0000** | **0.1643** | **0.0000** | **1.0000** |

## Focus metrics

- T6 abstention: `6/6` true positives; precision `0.2069`, recall `1.0000`.
- False abstention on non-T6: `23/140` = `0.1643`. This counts only strict `abstained`, not T7's intentional `not_in_corpus` status.
- T0 false-conflict rate: `0/18` = `0.0000`.
- T7 not-in-corpus recall: `13/13` = `1.0000`.
