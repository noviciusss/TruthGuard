# Corpus and gold adjudication (offline)

## Decision and provenance

All 24 original main T6 qids and both original wild T6 qids were re-adjudicated against all 35 documents. No rows were dropped: main remains 180 = 40 DEV + 140 TEST. The fixed-40 retains exactly its original qids and order, copying complete revised rows from main. No benchmark freeze was performed.

- The annual-limit history contains simultaneous **500000 and 600000**, both effective **2025-08-01**, at authority **2** (`CIR-2025-08-A` and `CIR-2025-08-B`). There is **no unique in-force historical value before the notice**. YAML/list order is not precedence.
- Explicit owner adjudication: **NOTICE-2025-11 uses fallback 500000 in both Filing and Operational rules**, effective **2025-11-01**, issued **2025-11-01**, authority **3**. This resolves the generated internal contradiction; it is not an inferred unique August winner.
- The current policy **POL-2026-V3** already states **600000 currency units per policy year**, effective **2026-01-01**, issued **2025-12-01**, authority **4**. It governs current whole-corpus questions. Relabel **T3 (numeric conflict), resolved, supersession**, winner **POL-2026-V3**. Resolution mode lives in the corpus manifest (`correct_mode`); the existing question schema represents it with `gold_status=resolved` plus winner/claims, and has no mode field.
- `wild-011` originally asserted there was no later notice breaking the tie. Its wording now asks about the complete corpus and current limit; retaining that false premise would be misleading. Other annual questions retain their wording.
- Generation now rejects ambiguous coeffective values rather than silently choosing the last entry. Existing age/plan-specific co-payment and room-rent schedules retain both explicitly scoped values; this also restores the omitted Standard room-rent schedule in CIR-2024-03/FAQ-2025-01 and Standard co-payment in FAQ-2025-01. No new fact or document was invented.

## Existing-fact search and semantic blocker

**0 defensible current whole-corpus T6 examples found; the target of at least 12 genuine TEST T6 examples cannot be met with existing evidence.** The historical August tie is real but is not a current whole-corpus tie. No queries were restricted to two circulars, time-shifted, or replaced by fabricated facts to retain T6. The original DEV/TEST assignments remain unchanged; all 24 original T6 labels become T3.

| Existing fact | Whole-corpus conflict review |
|---|---|
| waiting_period | Historical 30/45 days; amendment and later policy state 45, no unresolved top tie. |
| copay | 10% standard / 20% senior are distinct age scopes, not competing same-scope values. |
| claim_deadline | Historical 30/60 days; amendment and later policy give 60. |
| pre_existing_lookback | Historical 36/48 months; amendment and later policy give 48. |
| preauthorization | Planned prior approval and emergency 24-hour notification are contextual scopes. |
| room_rent | 1% Standard / 2% Premium are distinct plan scopes. |
| renewal_grace | All existing positions agree on 30 days. |
| grievance_timeline | Acknowledgement 3 business days and resolution 30 days are distinct phases. |
| network_cashless | Active network and approval; no competing eligibility rule found. |
| ambulance_limit | All existing positions give 10000 per hospitalization. |
| annual_limit | August 500000/600000 tie; November fallback 500000; current authority-4 policy 600000. |
| telemedicine | Existing positions agree on four consultations per year. |
| maternity | 24-month history is not asserted in existing corpus; Premium positions give 18 months. |
| exclusions | Cosmetic exclusion consistently retains medically necessary post-accident exception. |

This is evidence-based adjudication, not a claim that lexical scans prove semantic completeness. Missing cited headings and composed answers remain programmatically unverifiable; T7 semantic absence remains unverifiable even with no lexical hits. The audit inventories bounded same-fact/same-scope quantities, including dates and authority. Non-numeric semantics require review.

## Every changed qid (original → revised)

Old and new snapshots include type, status, answer, winner, documents, claims and source passages. Mode for every entry: **abstain → supersession**. Dataset occurrences are listed separately, including the overlapping fixed subset. `hand_verified` remains unchanged; this task does not claim an independent human review.

### questions.jsonl / t6-001 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-002 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-003 (dev)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-004 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-005 (dev)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-006 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-007 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-008 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-009 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-010 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-011 (dev)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-012 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-013 (dev)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-014 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-015 (dev)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-016 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-017 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-018 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-019 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-020 (dev)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-021 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-022 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-023 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### questions.jsonl / t6-024 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### wild.jsonl / wild-011 (wild)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit"], "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### wild.jsonl / wild-012 (wild)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11"], "gold_status": "abstained", "gold_winner_doc": null, "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing"], "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### eval_subset_40.jsonl / t6-001 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### eval_subset_40.jsonl / t6-008 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### eval_subset_40.jsonl / t6-016 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### eval_subset_40.jsonl / t6-018 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### eval_subset_40.jsonl / t6-021 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

### eval_subset_40.jsonl / t6-023 (test)

- Old: `{"gold_answer": null, "gold_claims": [], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_status": "abstained", "gold_winner_doc": null, "type": "T6"}`
- New: `{"gold_answer": "600000 currency units per policy year", "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.", "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."], "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "gold_status": "resolved", "gold_winner_doc": "POL-2026-V3", "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing", "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"], "type": "T3"}`

## Reproduce without resampling or freezing

```bash
TRUTHGUARD_OFFLINE=true PYTHONPATH=src .venv/bin/python -m bench.generate_corpus
TRUTHGUARD_OFFLINE=true PYTHONPATH=src .venv/bin/python -m bench.generate_questions --refresh-related
TRUTHGUARD_OFFLINE=true .venv/bin/python scripts/audit_corpus_programmatic.py
TRUTHGUARD_OFFLINE=true PYTHONPATH=.:src .venv/bin/python -m pytest -q tests/test_corpus.py tests/test_benchmark.py tests/test_programmatic_audit.py
```
