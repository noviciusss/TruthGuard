# TruthGuard pitch numbers

Every number below is a measured v2 value or an explicit v2 run count. The
default measured path is deterministic/offline with `HashEmbedder`; no provider
answered those rows. A live row says `not measured` when no result exists.

## Numbers safe to quote

| Number | Split / n | System | Path | Provider/model actually answering | Source |
|---|---|---|---|---|---|
| Conflict F1 `0.8835` | TEST / 146 | Full TruthGuard | deterministic/offline | none; HashEmbedder + deterministic critic | `reports/frozen_results.md` |
| Macro conflict F1 `0.6654` | TEST / 146 | Full TruthGuard | deterministic/offline | none; HashEmbedder + deterministic critic | `reports/frozen_results.md` |
| Status-correct answer rate `0.6781` | TEST / 146 | Full TruthGuard | deterministic/offline | none; HashEmbedder + deterministic critic | `reports/frozen_results.md`, `reports/accuracy_proxy_analysis.md` |
| Answer proxy `0.7123` | TEST / 146 | Full TruthGuard | deterministic/offline | none; HashEmbedder + deterministic critic | `reports/frozen_results.md` |
| T0 false-conflict rate `0/18 = 0.0000` | TEST T0 / 18 | Full TruthGuard | deterministic/offline | none | `reports/per_type_test.md` |
| T6 abstention recall `1.0000` | TEST T6 / 6 | Full TruthGuard | deterministic/offline | none | `reports/per_type_test.md` |
| T7 not-in-corpus recall `1.0000` | TEST T7 / 13 | Full TruthGuard | deterministic/offline | none | `reports/per_type_test.md` |
| Wild conflict F1 `0.5600` | wild / 22 | Full TruthGuard | deterministic/offline | none; HashEmbedder + deterministic critic | `reports/frozen_results.md` |
| TEST T3 share `36/146 = 24.7%` | TEST / 146 | Benchmark composition | deterministic/offline artifact | none | `reports/benchmark_freeze.md`, `reports/frozen_results.md` |
| Distinct factsheet keys `20` | corpus / 47 docs | Dataset metadata | deterministic/offline artifact | none | `data/factsheet/aurelia_facts_v2.yaml` |
| Distinct benchmark keys/classes `8` | DEV, TEST, wild, fixed v2 subset | Benchmark composition | deterministic/offline artifact | none | `reports/benchmark_freeze.md` |
| Full-system answer proxy `0.7123` | TEST / 146 | Full system ablation baseline | deterministic/offline | none; HashEmbedder | `reports/ablations_test.md` |
| no_critic answer proxy `0.8082` | TEST / 146 | Passage-only no-critic ablation | deterministic/offline | none; HashEmbedder | `reports/ablations_test.md`, `reports/accuracy_proxy_analysis.md` |
| Full-system status-correct rate `0.6781` | TEST / 146 | Full system ablation baseline | deterministic/offline | none; HashEmbedder | `reports/ablations_test.md`, `reports/accuracy_proxy_analysis.md` |
| no_critic status-correct rate `0.5411` | TEST / 146 | Passage-only no-critic ablation | deterministic/offline | none; HashEmbedder | `reports/ablations_test.md`, `reports/accuracy_proxy_analysis.md` |
| no_critic conflict F1 `0.0000` | TEST / 146 | Passage-only no-critic ablation | deterministic/offline | none; HashEmbedder | `reports/ablations_test.md` |
| no_supersession_graph conflict F1 `0.6782` | TEST / 146 | Graph ablation | deterministic/offline | none; HashEmbedder | `reports/ablations_test.md` |
| no_metadata_inference conflict F1 `0.8557` | TEST / 146 | Metadata ablation | deterministic/offline | none; HashEmbedder | `reports/ablations_test.md` |
| T6 fact keys `6` | v2 / 12 T6 rows | Genuine tie coverage | deterministic/offline artifact | none | `reports/benchmark_freeze.md` |
| Audit mechanical pass `138/212` | main + wild / 212 | Programmatic audit | deterministic/offline | none | `reports/corpus_audit_v2.md` |
| Audit failures `0/212` | main + wild / 212 | Programmatic audit | deterministic/offline | none | `reports/corpus_audit_v2.md` |
| Demo statuses verified `6/6` | scripted demo / 6 | Offline demo | deterministic/offline | none; v2 corpus | `reports/demo_output.md`, `docs/DEMO_SCRIPT.md` |

## Live-run accounting

| Number | Split / n | System | Path | Provider/model actually answering | Source |
|---|---|---|---|---|---|
| D1 completed `0/40`; unreached `40` | fixed v2 / 40 | LLM critic comparison | live not measured | none; no credential available | `reports/live_v2_status.md` |
| D2 completed `0` | fixed v2 / 40 | B0/B1 live baseline | live not measured | none | `reports/live_v2_status.md` |
| D3 completed `0/22` | wild / 22 | Live wild | live not measured | none | `reports/live_v2_status.md` |

## Do NOT claim

- Do not call the deterministic answer proxy semantic accuracy. It uses numeric,
  substring, and status rules; use the status-correct metric as the clearer
  conflict-aware companion, not as human semantic accuracy.
- Do not claim semantic provenance. The measured provenance metric is
  document-level ID overlap/citation presence, not supporting-span entailment.
- Do not claim production or real-world robustness from a synthetic corpus, a
  same-team templated benchmark, or 22-question wild set.
- Do not claim an as-of-date feature. User-facing as-of-date queries are not
  supported.
- Do not claim a live v2 LLM-critic, B0, B1, or wild result. No provider/model
  answered a v2 live row in this session.
- Do not claim `no_self_critique` or `no_conflict_seeking_expansion` TEST
  ablation numbers; they are LLM-path-only and were not measured on TEST.
- Do not claim that a fallback provider answered as the primary model. Any
  future live row must name the provider/model actually served.
- Do not use the historical v1 partial 7/40 Qwen run as a comparison. It had
  availability bias and different upstream contexts.
