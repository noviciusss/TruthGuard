# Frozen deterministic results — v2

V2 uses the additive genuine-T6 corpus and benchmark. Provider/model: none; deterministic pipeline only. Retrieval backend: HashEmbedder. No API calls.

## Micro and macro metrics

Micro metrics average every question. Macro metrics average the per-type metric values, giving each present type equal weight.

| Split | Questions | T0 | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T0 false conflicts | Micro conflict F1 | Macro conflict F1 | Micro answer | Macro answer | Micro mode | Macro mode | Abstention recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DEV | 44 | 2 | 7 | 6 | 12 | 7 | 3 | 4 | 3 | 0/2 (0.0000) | 0.9315 | 0.6891 | 0.7273 | 0.8214 | 0.7273 | 0.8214 | 1.0000 |
| TEST | 146 | 18 | 17 | 18 | 36 | 17 | 21 | 6 | 13 | 0/18 (0.0000) | 0.8835 | 0.6654 | 0.7123 | 0.8068 | 0.6781 | 0.7721 | 1.0000 |
| wild | 22 | 2 | 3 | 3 | 4 | 3 | 3 | 2 | 2 | 0/2 (0.0000) | 0.5600 | 0.4000 | 0.4091 | 0.4792 | 0.4091 | 0.4688 | 0.7500 |

## TEST distribution by fact key

The fact-key view uses explicit v2 `gold_fact_id` and conservative legacy mappings for v1 rows.

| Fact key | Questions | Types |
|---|---:|---|
| annual_limit | 18 | T3 |
| claim_deadline | 18 | T3 |
| copay | 18 | T2 |
| not_in_corpus | 13 | T7 |
| pre_existing_lookback | 17 | T4 |
| preauthorization | 21 | T5 |
| renewal_grace | 18 | T0 |
| t6_cashless_preauth_window | 1 | T6 |
| t6_claim_filing_deadline | 1 | T6 |
| t6_copay_rate | 1 | T6 |
| t6_grievance_response_window | 1 | T6 |
| t6_renewal_grace_period | 1 | T6 |
| t6_room_rent_cap | 1 | T6 |
| waiting_period | 17 | T1 |

## Per-type TEST metrics

| Type | n | Answer | Conflict F1 | Mode |
|---|---:|---:|---:|---:|
| T0 | 18 | 1.0000 | 0.0000 | 1.0000 |
| T1 | 17 | 0.7647 | 0.8667 | 0.7647 |
| T2 | 18 | 1.0000 | 0.8387 | 0.7222 |
| T3 | 36 | 0.2222 | 0.9254 | 0.2222 |
| T4 | 17 | 0.7059 | 0.8276 | 0.7059 |
| T5 | 21 | 0.7619 | 0.8649 | 0.7619 |
| T6 | 6 | 1.0000 | 1.0000 | 1.0000 |
| T7 | 13 | 1.0000 | 0.0000 | 1.0000 |

## Audit boundaries

- Provenance is document-level citation/overlap, not semantic supporting-span verification.
- The wild set remains a small manually written robustness set, not production accuracy.
- The fixed v2 subset is 40 questions: 2 T0, 6 each T1–T6, and 2 T7. Live critic/baseline results are not included here.
- Deterministic metrics exercise retrieval, synthesis, fact detection, conflict typing, supersession, metadata inference, and resolver behavior without a provider.
