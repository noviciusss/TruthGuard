# Programmatic corpus audit (offline)

## Reproduce

```bash
TRUTHGUARD_OFFLINE=true .venv/bin/python scripts/audit_corpus_programmatic.py
TRUTHGUARD_OFFLINE=true PYTHONPATH=.:src .venv/bin/python -m pytest -q tests/test_corpus.py tests/test_benchmark.py tests/test_programmatic_audit.py
```

Default outputs: `reports/corpus_audit_programmatic.md` and `.json`. Use `--root`, `--output`, and `--json-output` to select paths. No network, API, retrieval, critic, model, or pipeline execution. Exit 0 means completion; `--fail-on-findings` exits 1 for any fail/unverifiable finding. Invalid inputs exit 2.

## Interpretation and limits

Pass means only the named mechanical check passed, never semantic gold correctness. Question rollup: any failure → fail; otherwise any unverifiable check → unverifiable; otherwise pass. Metadata handling is counted separately, not folded into question gold counts. The fixed subset overlaps the main benchmark and is not additional unique evidence.

Value evidence is read from actual Markdown bodies/headings, not the factsheet, manifest answers, or runtime predictions. Matching is case/whitespace-normalized with word boundaries; raw case-sensitive hits are also recorded. Explicit section citations restrict matching to that section. Resolved answers must match the winner's cited evidence. Simple missing values fail when cited sections exist. Missing cited sections are unverifiable, never widened to the body or passed. Composed/paraphrased answers remain unverifiable even when full strings or quantities match; scenario arithmetic, exceptions, scope, and entailment require review. Literal claims and quantity matches are diagnostics in JSON, not substitute passes.

T7 searches every document with only the disclosed selected probe families. No hit is lexical evidence only and remains unverifiable; unknown subject families also remain unverifiable. A hit is a review candidate, not proof of coverage. Synonyms outside the probes, implicit statements, and semantic entailment are not detectable.

T0 scans lines containing the factsheet topic or bounded aliases (`renewal grace period`, `renewal may be completed`) and compares numeric durations only; unrelated durations do not count. For competition only, singular/plural and hyphenated durations such as `30-day` and `30 days` are treated alike. It cannot guarantee synonym completeness or adjudicate time/scope. T6 checks actual distinct annual-limit values, both issued/effective dates, and authority against loader and manifest. Its bounded topic aliases are factsheet topics; all matching positions are retained, including disagreements inside one document. For v2 T6, the audit checks equal effective/issued dates and authority, no supersession/amendment edge, exactly two physical documents, and no third same-fact document. Gold was revised by explicit corpus adjudication; see `reports/gold_changes.md`. The audit performs no runtime tuning or benchmark freeze.

## Measured question counts

| Dataset | Rows | Pass | Fail | Unverifiable |
|---|---:|---:|---:|---:|
| questions_v2.jsonl | 190 | 126 | 0 | 64 |
| wild_v2.jsonl | 22 | 12 | 0 | 10 |
| eval_subset_v2_40.jsonl | 40 | 26 | 0 | 14 |
| Unique (main + wild) | 212 | 138 | 0 | 74 |

## Per-type question counts

| Dataset | Type | Pass | Fail | Unverifiable |
|---|---|---:|---:|---:|
| questions_v2.jsonl | T0 | 20 | 0 | 0 |
| questions_v2.jsonl | T1 | 24 | 0 | 0 |
| questions_v2.jsonl | T2 | 0 | 0 | 24 |
| questions_v2.jsonl | T3 | 48 | 0 | 0 |
| questions_v2.jsonl | T4 | 24 | 0 | 0 |
| questions_v2.jsonl | T5 | 0 | 0 | 24 |
| questions_v2.jsonl | T6 | 10 | 0 | 0 |
| questions_v2.jsonl | T7 | 0 | 0 | 16 |
| wild_v2.jsonl | T0 | 2 | 0 | 0 |
| wild_v2.jsonl | T1 | 2 | 0 | 1 |
| wild_v2.jsonl | T2 | 0 | 0 | 3 |
| wild_v2.jsonl | T3 | 4 | 0 | 0 |
| wild_v2.jsonl | T4 | 2 | 0 | 1 |
| wild_v2.jsonl | T5 | 0 | 0 | 3 |
| wild_v2.jsonl | T6 | 2 | 0 | 0 |
| wild_v2.jsonl | T7 | 0 | 0 | 2 |
| eval_subset_v2_40.jsonl | T0 | 2 | 0 | 0 |
| eval_subset_v2_40.jsonl | T1 | 6 | 0 | 0 |
| eval_subset_v2_40.jsonl | T2 | 0 | 0 | 6 |
| eval_subset_v2_40.jsonl | T3 | 6 | 0 | 0 |
| eval_subset_v2_40.jsonl | T4 | 6 | 0 | 0 |
| eval_subset_v2_40.jsonl | T5 | 0 | 0 | 6 |
| eval_subset_v2_40.jsonl | T6 | 6 | 0 | 0 |
| eval_subset_v2_40.jsonl | T7 | 0 | 0 | 2 |
| Unique (main + wild) | T0 | 22 | 0 | 0 |
| Unique (main + wild) | T1 | 26 | 0 | 1 |
| Unique (main + wild) | T2 | 0 | 0 | 27 |
| Unique (main + wild) | T3 | 52 | 0 | 0 |
| Unique (main + wild) | T4 | 26 | 0 | 1 |
| Unique (main + wild) | T5 | 0 | 0 | 27 |
| Unique (main + wild) | T6 | 12 | 0 | 0 |
| Unique (main + wild) | T7 | 0 | 0 | 18 |

## Distinct fact keys by type and split

The v2 rows carry `gold_fact_id`; legacy rows use the conservative type-to-fact mapping documented in the JSON.

| Dataset | Type | Distinct keys | Fact keys |
|---|---|---:|---|
| questions_v2.jsonl | T0 | 1 | renewal_grace |
| questions_v2.jsonl | T1 | 1 | waiting_period |
| questions_v2.jsonl | T2 | 1 | copay |
| questions_v2.jsonl | T3 | 2 | annual_limit, claim_deadline |
| questions_v2.jsonl | T4 | 1 | pre_existing_lookback |
| questions_v2.jsonl | T5 | 1 | preauthorization |
| questions_v2.jsonl | T6 | 6 | t6_cashless_preauth_window, t6_claim_filing_deadline, t6_copay_rate, t6_grievance_response_window, t6_renewal_grace_period, t6_room_rent_cap |
| questions_v2.jsonl | T7 | 0 | none |
| wild_v2.jsonl | T0 | 1 | renewal_grace |
| wild_v2.jsonl | T1 | 1 | waiting_period |
| wild_v2.jsonl | T2 | 1 | copay |
| wild_v2.jsonl | T3 | 1 | claim_deadline |
| wild_v2.jsonl | T4 | 1 | pre_existing_lookback |
| wild_v2.jsonl | T5 | 1 | preauthorization |
| wild_v2.jsonl | T6 | 2 | t6_copay_rate, t6_renewal_grace_period |
| wild_v2.jsonl | T7 | 0 | none |
| eval_subset_v2_40.jsonl | T0 | 1 | renewal_grace |
| eval_subset_v2_40.jsonl | T1 | 1 | waiting_period |
| eval_subset_v2_40.jsonl | T2 | 1 | copay |
| eval_subset_v2_40.jsonl | T3 | 2 | annual_limit, claim_deadline |
| eval_subset_v2_40.jsonl | T4 | 1 | pre_existing_lookback |
| eval_subset_v2_40.jsonl | T5 | 1 | preauthorization |
| eval_subset_v2_40.jsonl | T6 | 6 | t6_cashless_preauth_window, t6_claim_filing_deadline, t6_copay_rate, t6_grievance_response_window, t6_renewal_grace_period, t6_room_rent_cap |
| eval_subset_v2_40.jsonl | T7 | 0 | none |
| Unique split=dev | all types | 11 | annual_limit, claim_deadline, copay, pre_existing_lookback, preauthorization, renewal_grace, t6_claim_filing_deadline, t6_copay_rate, t6_grievance_response_window, t6_room_rent_cap, waiting_period |
| Unique split=test | all types | 13 | annual_limit, claim_deadline, copay, pre_existing_lookback, preauthorization, renewal_grace, t6_cashless_preauth_window, t6_claim_filing_deadline, t6_copay_rate, t6_grievance_response_window, t6_renewal_grace_period, t6_room_rent_cap, waiting_period |
| Unique split=unspecified | all types | 8 | claim_deadline, copay, pre_existing_lookback, preauthorization, renewal_grace, t6_copay_rate, t6_renewal_grace_period, waiting_period |

## Check counts and exact affected qids

### questions_v2.jsonl

| Check | Pass | Fail | Unverifiable |
|---|---:|---:|---:|
| cited_sources | 190 | 0 | 0 |
| gold_value_presence | 116 | 0 | 48 |
| t0_same_fact_competition | 20 | 0 | 0 |
| t6_global_abstention | 10 | 0 | 0 |
| t6_gold_shape | 10 | 0 | 0 |
| t6_no_third_document | 10 | 0 | 0 |
| t6_same_date_same_authority | 10 | 0 | 0 |
| t7_absence | 0 | 0 | 16 |
| t7_gold_shape | 16 | 0 | 0 |

**Exact fail qids (0):** none

**Exact unverifiable qids (64):** `t2-006`, `t5-017`, `t2-018`, `t7-001`, `t2-019`, `t7-005`, `t5-002`, `t2-009`, `t2-010`, `t2-014`, `t7-004`, `t5-022`, `t7-002`, `t5-021`, `t5-007`, `t2-012`, `t2-005`, `t5-019`, `t5-020`, `t2-002`, `t5-008`, `t2-024`, `t7-011`, `t2-004`, `t5-010`, `t7-006`, `t5-005`, `t2-022`, `t5-011`, `t2-016`, `t7-016`, `t5-015`, `t2-021`, `t5-003`, `t2-017`, `t5-018`, `t5-009`, `t5-024`, `t5-001`, `t7-013`, `t7-008`, `t2-020`, `t5-004`, `t7-015`, `t7-010`, `t5-023`, `t5-014`, `t7-009`, `t2-003`, `t2-023`, `t2-007`, `t2-013`, `t2-011`, `t7-012`, `t7-014`, `t7-007`, `t2-008`, `t5-013`, `t5-012`, `t5-016`, `t2-001`, `t7-003`, `t5-006`, `t2-015`

- **gold_value_presence:** Composed/paraphrased answer remains unverifiable even if a full string or all quantities occur. Qids: `t2-006`, `t5-017`, `t2-018`, `t2-019`, `t5-002`, `t2-009`, `t2-010`, `t2-014`, `t5-022`, `t5-021`, `t5-007`, `t2-012`, `t2-005`, `t5-019`, `t5-020`, `t2-002`, `t5-008`, `t2-024`, `t2-004`, `t5-010`, `t5-005`, `t2-022`, `t5-011`, `t2-016`, `t5-015`, `t2-021`, `t5-003`, `t2-017`, `t5-018`, `t5-009`, `t5-024`, `t5-001`, `t2-020`, `t5-004`, `t5-023`, `t5-014`, `t2-003`, `t2-023`, `t2-007`, `t2-013`, `t2-011`, `t2-008`, `t5-013`, `t5-012`, `t5-016`, `t2-001`, `t5-006`, `t2-015`

- **t7_absence:** No selected lexical probe hit; semantic absence is not provable by this scan. Qids: `t7-001`, `t7-005`, `t7-004`, `t7-002`, `t7-011`, `t7-006`, `t7-016`, `t7-013`, `t7-008`, `t7-015`, `t7-010`, `t7-009`, `t7-012`, `t7-014`, `t7-007`, `t7-003`
### wild_v2.jsonl

| Check | Pass | Fail | Unverifiable |
|---|---:|---:|---:|
| cited_sources | 22 | 0 | 0 |
| gold_value_presence | 10 | 0 | 8 |
| t0_same_fact_competition | 2 | 0 | 0 |
| t6_global_abstention | 2 | 0 | 0 |
| t6_gold_shape | 2 | 0 | 0 |
| t6_no_third_document | 2 | 0 | 0 |
| t6_same_date_same_authority | 2 | 0 | 0 |
| t7_absence | 0 | 0 | 2 |
| t7_gold_shape | 2 | 0 | 0 |

**Exact fail qids (0):** none

**Exact unverifiable qids (10):** `wild-003`, `wild-004`, `wild-009`, `wild-010`, `wild-015`, `wild-016`, `wild-017`, `wild-018`, `wild-019`, `wild-020`

- **gold_value_presence:** Composed/paraphrased answer remains unverifiable even if a full string or all quantities occur. Qids: `wild-003`, `wild-004`, `wild-009`, `wild-010`, `wild-017`, `wild-018`, `wild-019`, `wild-020`

- **t7_absence:** No selected lexical probe hit; semantic absence is not provable by this scan. Qids: `wild-015`, `wild-016`
### eval_subset_v2_40.jsonl

| Check | Pass | Fail | Unverifiable |
|---|---:|---:|---:|
| cited_sources | 40 | 0 | 0 |
| gold_value_presence | 20 | 0 | 12 |
| subset_membership | 40 | 0 | 0 |
| t0_same_fact_competition | 2 | 0 | 0 |
| t6_global_abstention | 6 | 0 | 0 |
| t6_gold_shape | 6 | 0 | 0 |
| t6_no_third_document | 6 | 0 | 0 |
| t6_same_date_same_authority | 6 | 0 | 0 |
| t7_absence | 0 | 0 | 2 |
| t7_gold_shape | 2 | 0 | 0 |

**Exact fail qids (0):** none

**Exact unverifiable qids (14):** `t2-002`, `t2-004`, `t2-005`, `t2-017`, `t2-022`, `t2-024`, `t5-001`, `t5-004`, `t5-005`, `t5-015`, `t5-016`, `t5-020`, `t7-007`, `t7-012`

- **gold_value_presence:** Composed/paraphrased answer remains unverifiable even if a full string or all quantities occur. Qids: `t2-002`, `t2-004`, `t2-005`, `t2-017`, `t2-022`, `t2-024`, `t5-001`, `t5-004`, `t5-005`, `t5-015`, `t5-016`, `t5-020`

- **t7_absence:** No selected lexical probe hit; semantic absence is not provable by this scan. Qids: `t7-007`, `t7-012`

## Metadata handling against manifest

All documents: `{'pass': 47, 'fail': 0, 'unverifiable': 0}`. Corrupted only: `{'pass': 14, 'fail': 0, 'unverifiable': 0}`.

Compared identity, title, type, version, issued/effective dates, authority, supersedes, and amends. A corrupted header version `0.0` must become null with metadata_confidence `0.0`: this is an accepted information loss, **not recovered-version success**. The expected manifest version is comparison-only and must never be copied into loaded metadata. Other physical-field differences still fail. Derived annotations are disclosed in JSON; confidence zero is required for the accepted unknown-version case.

Accepted unknown versions: **7** (version_recovered=false).

| Document | Corruption | Result | Outcome | Physical-field differences |
|---|---|---|---|---|
| POL-2024-V1 | missing_effective | pass | physical_fields_compared | `{}` |
| POL-2025-V2 | wrong_version | pass | accepted_unknown_version | `{"version": {"expected": "2.0", "loaded": null}}` |
| POL-2026-V3 | none | pass | physical_fields_compared | `{}` |
| AMD-2025-03 | none | pass | physical_fields_compared | `{}` |
| AMD-2025-04 | none | pass | physical_fields_compared | `{}` |
| AMD-2025-05 | missing_effective | pass | physical_fields_compared | `{}` |
| AMD-2025-07 | wrong_version | pass | accepted_unknown_version | `{"version": {"expected": "2025-07", "loaded": null}}` |
| AMD-2025-09 | none | pass | physical_fields_compared | `{}` |
| AMD-2026-01 | none | pass | physical_fields_compared | `{}` |
| AMD-2026-02 | none | pass | physical_fields_compared | `{}` |
| AMD-2026-03 | missing_effective | pass | physical_fields_compared | `{}` |
| AMD-2026-04 | wrong_version | pass | accepted_unknown_version | `{"version": {"expected": "2026-04", "loaded": null}}` |
| CIR-2024-01 | none | pass | physical_fields_compared | `{}` |
| CIR-2024-02 | none | pass | physical_fields_compared | `{}` |
| CIR-2024-03 | none | pass | physical_fields_compared | `{}` |
| CIR-2025-06 | missing_effective | pass | physical_fields_compared | `{}` |
| CIR-2025-08-A | wrong_version | pass | accepted_unknown_version | `{"version": {"expected": "2025/08-A", "loaded": null}}` |
| CIR-2025-08-B | none | pass | physical_fields_compared | `{}` |
| CIR-2025-10 | none | pass | physical_fields_compared | `{}` |
| CIR-2026-01 | none | pass | physical_fields_compared | `{}` |
| CIR-2026-02 | missing_effective | pass | physical_fields_compared | `{}` |
| FAQ-2024-01 | wrong_version | pass | accepted_unknown_version | `{"version": {"expected": "2024.1", "loaded": null}}` |
| FAQ-2024-02 | none | pass | physical_fields_compared | `{}` |
| FAQ-2025-01 | none | pass | physical_fields_compared | `{}` |
| FAQ-2025-06 | none | pass | physical_fields_compared | `{}` |
| FAQ-2026-01 | missing_effective | pass | physical_fields_compared | `{}` |
| FAQ-2026-02 | wrong_version | pass | accepted_unknown_version | `{"version": {"expected": "2026.2", "loaded": null}}` |
| MAN-2024-CLAIMS | none | pass | physical_fields_compared | `{}` |
| MAN-2025-CLAIMS | none | pass | physical_fields_compared | `{}` |
| MAN-2025-CASHLESS | none | pass | physical_fields_compared | `{}` |
| MAN-2026-GRIEVANCE | missing_effective | pass | physical_fields_compared | `{}` |
| NOTICE-2024-01 | wrong_version | pass | accepted_unknown_version | `{"version": {"expected": "2024/01", "loaded": null}}` |
| NOTICE-2025-02 | none | pass | physical_fields_compared | `{}` |
| NOTICE-2025-11 | none | pass | physical_fields_compared | `{}` |
| NOTICE-2026-01 | none | pass | physical_fields_compared | `{}` |
| CIR-2026-T6-ROOM-A | none | pass | physical_fields_compared | `{}` |
| CIR-2026-T6-ROOM-B | none | pass | physical_fields_compared | `{}` |
| CIR-2026-T6-COPAY-A | none | pass | physical_fields_compared | `{}` |
| CIR-2026-T6-COPAY-B | none | pass | physical_fields_compared | `{}` |
| CIR-2026-T6-GRV-A | none | pass | physical_fields_compared | `{}` |
| CIR-2026-T6-GRV-B | none | pass | physical_fields_compared | `{}` |
| CIR-2026-T6-CLAIM-A | none | pass | physical_fields_compared | `{}` |
| CIR-2026-T6-CLAIM-B | none | pass | physical_fields_compared | `{}` |
| CIR-2026-T6-PREAUTH-A | none | pass | physical_fields_compared | `{}` |
| CIR-2026-T6-PREAUTH-B | none | pass | physical_fields_compared | `{}` |
| CIR-2026-T6-RENEW-A | none | pass | physical_fields_compared | `{}` |
| CIR-2026-T6-RENEW-B | none | pass | physical_fields_compared | `{}` |

### Exact qids citing failed metadata documents

These are metadata-impact qids, separate from question gold failures above.


## T7 lexical probes

```json
{
  "hearing aid": [
    "hearing[\\s-]*aids?",
    "batter(?:y|ies)"
  ],
  "robotic home surgery": [
    "robot(?:ic)?",
    "home[\\s-]+surg(?:ery|ical)"
  ],
  "gene therapy": [
    "gene[\\s-]+therap(?:y|ies)",
    "genetic[\\s-]+therap(?:y|ies)"
  ],
  "underwater rehabilitation": [
    "underwater",
    "aquatic",
    "hydrotherap(?:y|ies)"
  ]
}
```

## Evidence and adjudication limits

1. **Composed gold:** review all `gold_value_presence` unverifiable qids listed above. Check clauses, scope, exception, and scenario arithmetic against the exact cited sections in JSON. Safe proposal: add independently reviewed atomic evidence mappings or correct a section citation if it points to the wrong passage. Missing full strings must not be relabeled as literal passes.

2. **Annual-limit adjudication:** both sections of NOTICE-2025-11 use the owner-adjudicated 500000 fallback, effective 2025-11-01, authority 3. The simultaneous August 500000/600000 history has no unique pre-notice value. Current POL-2026-V3 gives 600000 at authority 4, effective 2026-01-01. All original annual-limit T6 qids now have T3/resolved gold with supersession mode recorded in the manifest. No 12 genuine current whole-corpus TEST T6 examples exist in the reviewed evidence; zero were retained. No pair-only query scoping or invented evidence was used. The full per-qid old/new ledger and existing-fact review are in `reports/gold_changes.md`.

3. **Metadata:** safe unknown versions are explicitly accepted losses with confidence zero, not successful version recovery. An unsupported non-null corrupted version fails, even if it happens to equal manifest gold.

4. **T7:** a human must adjudicate semantic absence for every T7 qid; the lexical no-hit result is insufficient. T0 passes are bounded topic/alias scans, not a proof that no paraphrased competing rule exists.

5. **Intra-document same-fact AND same-scope scan:** bounded topic/heading aliases and numeric quantities are listed in JSON, including exact lines, dates and authority. 10% Standard / 20% senior, 1% Standard / 2% Premium, and acknowledgement / resolution deadlines are separate scopes, not internal contradictions. A one-value pass means only quantitative consistency for the scanned scope; missing quantities, unknown scopes and non-numeric semantics remain unverifiable.

## Intra-document quantitative consistency

Counts by document/fact/scope group: `{'pass': 73, 'fail': 0, 'unverifiable': 13}`.

| Document | Fact | Scope | Values | Result | Effective | Issued | Authority |
|---|---|---|---|---|---|---|---:|
| AMD-2025-03 | waiting_period | standard plan, non-accidental hospitalization | 45 days | pass | 2025-03-01 | 2025-02-15 | 3 |
| AMD-2025-04 | claim_deadline | reimbursement claims | 60 days | pass | 2025-04-15 | 2025-04-01 | 3 |
| AMD-2025-05 | pre_existing_lookback | conditions diagnosed or treated before policy start | 48 months | pass | 2025-05-01 | 2025-04-20 | 3 |
| AMD-2025-07 | maternity | premium plan | 18 months | pass | 2025-07-01 | 2025-06-15 | 3 |
| AMD-2025-09 | network_cashless | planned treatment at an aurelia network hospital | non-numeric | unverifiable | 2025-09-01 | 2025-08-15 | 3 |
| AMD-2026-01 | telemedicine | active members | four telemedicine consultations | pass | 2026-01-01 | 2025-12-15 | 3 |
| AMD-2026-02 | grievance_timeline | acknowledgement | 3 business days | pass | 2026-02-01 | 2026-01-15 | 3 |
| AMD-2026-02 | grievance_timeline | resolution | 30 days | pass | 2026-02-01 | 2026-01-15 | 3 |
| AMD-2026-03 | ambulance_limit | covered hospitalization | 10000 currency units | pass | 2026-03-01 | 2026-02-15 | 3 |
| AMD-2026-04 | exclusions | treatment primarily for cosmetic enhancement | non-numeric | unverifiable | 2026-04-01 | 2026-03-15 | 3 |
| CIR-2024-01 | renewal_grace | all active plans | 30 days | pass | 2024-02-01 | 2024-01-20 | 2 |
| CIR-2024-02 | copay | senior members aged 60 and above | 20% | pass | 2024-03-01 | 2024-02-15 | 2 |
| CIR-2024-02 | copay | standard plan | 10% | pass | 2024-03-01 | 2024-02-15 | 2 |
| CIR-2024-03 | room_rent | premium plan | 2% | pass | 2024-04-01 | 2024-03-20 | 2 |
| CIR-2024-03 | room_rent | standard plan | 1% | pass | 2024-04-01 | 2024-03-20 | 2 |
| CIR-2025-06 | preauthorization | emergency notification | 24 hours | pass | 2025-06-01 | 2025-05-20 | 2 |
| CIR-2025-08-A | annual_limit | standard plan | 500000 currency units | pass | 2025-08-01 | 2025-08-01 | 2 |
| CIR-2025-08-B | annual_limit | standard plan | 600000 currency units | pass | 2025-08-01 | 2025-08-01 | 2 |
| CIR-2025-10 | renewal_grace | all active plans | 30 days | pass | 2025-10-01 | 2025-09-15 | 2 |
| CIR-2026-01 | telemedicine | active members | four telemedicine consultations | pass | 2026-01-10 | 2025-12-20 | 2 |
| CIR-2026-02 | ambulance_limit | covered hospitalization | 10000 currency units | pass | 2026-02-10 | 2026-01-25 | 2 |
| CIR-2026-T6-CLAIM-A | claim_deadline | reimbursement claims | 45 days | pass | 2026-08-01 | 2026-07-15 | 2 |
| CIR-2026-T6-CLAIM-A | t6_claim_filing_deadline | standard plan reimbursement claims | 45 days | pass | 2026-08-01 | 2026-07-15 | 2 |
| CIR-2026-T6-CLAIM-B | claim_deadline | reimbursement claims | 75 days | pass | 2026-08-01 | 2026-07-15 | 2 |
| CIR-2026-T6-CLAIM-B | t6_claim_filing_deadline | standard plan reimbursement claims | 75 days | pass | 2026-08-01 | 2026-07-15 | 2 |
| CIR-2026-T6-COPAY-A | copay | standard plan | 15% | pass | 2026-06-01 | 2026-05-15 | 2 |
| CIR-2026-T6-COPAY-A | t6_copay_rate | aurelia standard plan members | 15% | pass | 2026-06-01 | 2026-05-15 | 2 |
| CIR-2026-T6-COPAY-B | copay | standard plan | 25% | pass | 2026-06-01 | 2026-05-15 | 2 |
| CIR-2026-T6-COPAY-B | t6_copay_rate | aurelia standard plan members | 25% | pass | 2026-06-01 | 2026-05-15 | 2 |
| CIR-2026-T6-GRV-A | grievance_timeline | unspecified phase | 15 days | unverifiable | 2026-07-01 | 2026-06-15 | 2 |
| CIR-2026-T6-GRV-A | t6_grievance_response_window | standard plan member grievances | 15 days | pass | 2026-07-01 | 2026-06-15 | 2 |
| CIR-2026-T6-GRV-B | grievance_timeline | unspecified phase | 30 days | unverifiable | 2026-07-01 | 2026-06-15 | 2 |
| CIR-2026-T6-GRV-B | t6_grievance_response_window | standard plan member grievances | 30 days | pass | 2026-07-01 | 2026-06-15 | 2 |
| CIR-2026-T6-PREAUTH-A | preauthorization | unspecified admission | 2 hours | unverifiable | 2026-09-01 | 2026-08-15 | 2 |
| CIR-2026-T6-PREAUTH-A | t6_cashless_preauth_window | standard plan planned admissions | 2 hours | pass | 2026-09-01 | 2026-08-15 | 2 |
| CIR-2026-T6-PREAUTH-B | preauthorization | unspecified admission | 6 hours | unverifiable | 2026-09-01 | 2026-08-15 | 2 |
| CIR-2026-T6-PREAUTH-B | t6_cashless_preauth_window | standard plan planned admissions | 6 hours | pass | 2026-09-01 | 2026-08-15 | 2 |
| CIR-2026-T6-RENEW-A | renewal_grace | all active plans | 14 days | pass | 2026-10-01 | 2026-09-15 | 2 |
| CIR-2026-T6-RENEW-A | t6_renewal_grace_period | standard plan renewal reinstatement | 14 days | pass | 2026-10-01 | 2026-09-15 | 2 |
| CIR-2026-T6-RENEW-B | renewal_grace | all active plans | 21 days | pass | 2026-10-01 | 2026-09-15 | 2 |
| CIR-2026-T6-RENEW-B | t6_renewal_grace_period | standard plan renewal reinstatement | 21 days | pass | 2026-10-01 | 2026-09-15 | 2 |
| CIR-2026-T6-ROOM-A | room_rent | standard plan | 1% | pass | 2026-05-01 | 2026-04-15 | 2 |
| CIR-2026-T6-ROOM-A | t6_room_rent_cap | aurelia standard plan inpatient room | 1% | pass | 2026-05-01 | 2026-04-15 | 2 |
| CIR-2026-T6-ROOM-B | room_rent | standard plan | 2% | pass | 2026-05-01 | 2026-04-15 | 2 |
| CIR-2026-T6-ROOM-B | t6_room_rent_cap | aurelia standard plan inpatient room | 2% | pass | 2026-05-01 | 2026-04-15 | 2 |
| FAQ-2024-01 | waiting_period | standard plan, non-accidental hospitalization | 30 days | pass | 2024-02-15 | 2024-02-15 | 0 |
| FAQ-2024-02 | pre_existing_lookback | conditions diagnosed or treated before policy start | 36 months | pass | 2024-03-15 | 2024-03-15 | 0 |
| FAQ-2025-01 | copay | senior members aged 60 and above | 20% | pass | 2025-01-15 | 2025-01-15 | 0 |
| FAQ-2025-01 | copay | standard plan | 10% | pass | 2025-01-15 | 2025-01-15 | 0 |
| FAQ-2025-01 | copay | unspecified age/plan | non-numeric | unverifiable | 2025-01-15 | 2025-01-15 | 0 |
| FAQ-2025-01 | room_rent | premium plan | 2% | pass | 2025-01-15 | 2025-01-15 | 0 |
| FAQ-2025-01 | room_rent | standard plan | 1% | pass | 2025-01-15 | 2025-01-15 | 0 |
| FAQ-2025-06 | maternity | premium plan | 18 months | pass | 2025-06-15 | 2025-06-15 | 0 |
| FAQ-2025-06 | pre_existing_lookback | conditions diagnosed or treated before policy start | 48 months | pass | 2025-06-15 | 2025-06-15 | 0 |
| FAQ-2025-06 | waiting_period | standard plan, non-accidental hospitalization | 45 days | pass | 2025-06-15 | 2025-06-15 | 0 |
| FAQ-2026-01 | renewal_grace | all active plans | 30 days | pass | 2026-01-20 | 2026-01-20 | 0 |
| FAQ-2026-02 | network_cashless | planned treatment at an aurelia network hospital | non-numeric | unverifiable | 2026-02-20 | 2026-02-20 | 0 |
| FAQ-2026-02 | telemedicine | active members | four telemedicine consultations | pass | 2026-02-20 | 2026-02-20 | 0 |
| MAN-2024-CLAIMS | claim_deadline | reimbursement claims | 30 days | pass | 2024-01-10 | 2024-01-10 | 1 |
| MAN-2024-CLAIMS | exclusions | treatment primarily for cosmetic enhancement | non-numeric | unverifiable | 2024-01-10 | 2024-01-10 | 1 |
| MAN-2025-CASHLESS | network_cashless | planned treatment at an aurelia network hospital | non-numeric | unverifiable | 2025-06-15 | 2025-06-15 | 1 |
| MAN-2025-CASHLESS | preauthorization | emergency notification | 24 hours | pass | 2025-06-15 | 2025-06-15 | 1 |
| MAN-2025-CLAIMS | claim_deadline | reimbursement claims | 60 days | pass | 2025-05-15 | 2025-05-15 | 1 |
| MAN-2026-GRIEVANCE | grievance_timeline | acknowledgement | 3 business days | pass | 2026-02-15 | 2026-02-15 | 1 |
| MAN-2026-GRIEVANCE | grievance_timeline | resolution | 30 days | pass | 2026-02-15 | 2026-02-15 | 1 |
| NOTICE-2024-01 | exclusions | treatment primarily for cosmetic enhancement | non-numeric | unverifiable | 2024-05-01 | 2024-05-01 | 3 |
| NOTICE-2025-02 | preauthorization | emergency notification | 24 hours | pass | 2025-06-05 | 2025-06-05 | 3 |
| NOTICE-2025-11 | annual_limit | standard plan | 500000 currency units | pass | 2025-11-01 | 2025-11-01 | 3 |
| NOTICE-2026-01 | grievance_timeline | acknowledgement | 3 business days | pass | 2026-01-05 | 2026-01-05 | 3 |
| NOTICE-2026-01 | grievance_timeline | resolution | 30 days | pass | 2026-01-05 | 2026-01-05 | 3 |
| POL-2024-V1 | claim_deadline | reimbursement claims | 30 days | pass | 2024-01-01 | 2023-12-15 | 4 |
| POL-2024-V1 | copay | standard plan | 10% | pass | 2024-01-01 | 2023-12-15 | 4 |
| POL-2024-V1 | pre_existing_lookback | conditions diagnosed or treated before policy start | 36 months | pass | 2024-01-01 | 2023-12-15 | 4 |
| POL-2024-V1 | preauthorization | planned and emergency admissions | non-numeric | unverifiable | 2024-01-01 | 2023-12-15 | 4 |
| POL-2024-V1 | waiting_period | standard plan, non-accidental hospitalization | 30 days | pass | 2024-01-01 | 2023-12-15 | 4 |
| POL-2025-V2 | claim_deadline | reimbursement claims | 60 days | pass | 2025-06-01 | 2025-05-01 | 4 |
| POL-2025-V2 | copay | standard plan | 10% | pass | 2025-06-01 | 2025-05-01 | 4 |
| POL-2025-V2 | pre_existing_lookback | conditions diagnosed or treated before policy start | 48 months | pass | 2025-06-01 | 2025-05-01 | 4 |
| POL-2025-V2 | preauthorization | planned and emergency admissions | non-numeric | unverifiable | 2025-06-01 | 2025-05-01 | 4 |
| POL-2025-V2 | waiting_period | standard plan, non-accidental hospitalization | 45 days | pass | 2025-06-01 | 2025-05-01 | 4 |
| POL-2026-V3 | annual_limit | standard plan | 600000 currency units | pass | 2026-01-01 | 2025-12-01 | 4 |
| POL-2026-V3 | grievance_timeline | acknowledgement | 3 business days | pass | 2026-01-01 | 2025-12-01 | 4 |
| POL-2026-V3 | grievance_timeline | resolution | 30 days | pass | 2026-01-01 | 2025-12-01 | 4 |
| POL-2026-V3 | maternity | premium plan | 18 months | pass | 2026-01-01 | 2025-12-01 | 4 |
| POL-2026-V3 | renewal_grace | all active plans | 30 days | pass | 2026-01-01 | 2025-12-01 | 4 |
| POL-2026-V3 | telemedicine | active members | four telemedicine consultations | pass | 2026-01-01 | 2025-12-01 | 4 |

### T0 and T6 actual corpus positions

- `CIR-2024-01:17` (effective 2024-02-01, issued 2024-01-20, authority 2): A renewal may be completed within 30 days after the due date.
- `CIR-2024-01:21` (effective 2024-02-01, issued 2024-01-20, authority 2): - **renewal grace period** (all active plans): 30 days after renewal due date.
- `CIR-2025-10:17` (effective 2025-10-01, issued 2025-09-15, authority 2): The 30-day renewal grace period applies to all active plans.
- `CIR-2025-10:21` (effective 2025-10-01, issued 2025-09-15, authority 2): - **renewal grace period** (all active plans): 30 days after renewal due date.
- `FAQ-2026-01:17` (effective 2026-01-20, issued 2026-01-20, authority 0): Members have a 30-day renewal grace period.
- `FAQ-2026-01:21` (effective 2026-01-20, issued 2026-01-20, authority 0): - **renewal grace period** (all active plans): 30 days after renewal due date.
- `POL-2026-V3:25` (effective 2026-01-01, issued 2025-12-01, authority 4): - **renewal grace period** (all active plans): 30 days after renewal due date.
- Pair `CIR-2026-T6-ROOM-A` / `CIR-2026-T6-ROOM-B`: values `[['1%'], ['2%']]`, effective `['2026-05-01', '2026-05-01']`, issued `['2026-04-15', '2026-04-15']`, authority `[2, 2]`; loaded tie `True`, manifest tie `True`, loaded agrees with manifest `True`.
- Pair `CIR-2026-T6-COPAY-A` / `CIR-2026-T6-COPAY-B`: values `[['15%'], ['25%']]`, effective `['2026-06-01', '2026-06-01']`, issued `['2026-05-15', '2026-05-15']`, authority `[2, 2]`; loaded tie `True`, manifest tie `True`, loaded agrees with manifest `True`.
- Pair `CIR-2026-T6-GRV-A` / `CIR-2026-T6-GRV-B`: values `[['15 days'], ['30 days']]`, effective `['2026-07-01', '2026-07-01']`, issued `['2026-06-15', '2026-06-15']`, authority `[2, 2]`; loaded tie `True`, manifest tie `True`, loaded agrees with manifest `True`.
- Pair `CIR-2026-T6-CLAIM-A` / `CIR-2026-T6-CLAIM-B`: values `[['45 days'], ['75 days']]`, effective `['2026-08-01', '2026-08-01']`, issued `['2026-07-15', '2026-07-15']`, authority `[2, 2]`; loaded tie `True`, manifest tie `True`, loaded agrees with manifest `True`.
- Pair `CIR-2026-T6-PREAUTH-A` / `CIR-2026-T6-PREAUTH-B`: values `[['2 hours'], ['6 hours']]`, effective `['2026-09-01', '2026-09-01']`, issued `['2026-08-15', '2026-08-15']`, authority `[2, 2]`; loaded tie `True`, manifest tie `True`, loaded agrees with manifest `True`.
- Pair `CIR-2026-T6-RENEW-A` / `CIR-2026-T6-RENEW-B`: values `[['14 days'], ['21 days']]`, effective `['2026-10-01', '2026-10-01']`, issued `['2026-09-15', '2026-09-15']`, authority `[2, 2]`; loaded tie `True`, manifest tie `True`, loaded agrees with manifest `True`.

## Input SHA-256 fingerprints

The companion JSON records every qid/check and all input hashes; hashes below make reruns auditable.

```text
dbe6c590a04f47740339f19c9af3c8714cbcdf37dd0b1d0899723de28e725bb5  config.yaml
d7c23376f78bff192422c5b5fffb45bb123816962d2f377ef2f4033743cf9919  data/benchmark/eval_subset_v2_40.jsonl
d0ffef1936bc9804a8359f456ed30c981d9e6baa6d7339505df8653ca744e87a  data/benchmark/questions_v2.jsonl
8e684bdefe8ba9f6b0309440fc7c1ec5a6e3180b06b4741fd22825752a42a1b8  data/benchmark/wild_v2.jsonl
35163301466f57a2ea7d85cb0c0f3aeab8a78e53ec524b6cf54b8a24bdfe5471  data/corpus_v2/AMD-2025-03.md
4c4dc6c69468f1c76b511328fde9294fd9a56db8ad857dacb6d7cf5f6912ac43  data/corpus_v2/AMD-2025-04.md
a494e618df6f8fe1fa4582730b533d1506c96e4d1396002abe0cbbbc8945917b  data/corpus_v2/AMD-2025-05.md
41d73ceb914c973f348167b22f8437b16b0a4bbfb14dd54312236a873f1cbe06  data/corpus_v2/AMD-2025-07.md
7b3e40959566b2dfa2550fcde4b35cbf2ae40058fb77532a72de10a2f095dfab  data/corpus_v2/AMD-2025-09.md
2ae6be528127234b8c26a195d0ddbe341b78d349e84187937e24cf7717c75843  data/corpus_v2/AMD-2026-01.md
c22a4fab807b314c7e5bbd49607c1b63249613f29afe1ff3be03933db8c0e08c  data/corpus_v2/AMD-2026-02.md
9b4586ead0e1022830c643bfda1939afaa00c43a6eee8d2b43452b4d78c06cf8  data/corpus_v2/AMD-2026-03.md
4df0be9cc81b1dd74e050cea56645b67b94841f6eb76463e39db3f64b1707e1f  data/corpus_v2/AMD-2026-04.md
e2d9382a8c285395c0451468dbfac59040d82b0d913bf8a1494ac1d9c085a9b7  data/corpus_v2/CIR-2024-01.md
b22f8862e8f53e9e02fd383931587e89d4a8dd40adc066e376eddf83ac73f02b  data/corpus_v2/CIR-2024-02.md
db29d2c5d7fcd408efce1f8a0e23169e2a3345de4d3cec2480606b93e228c03a  data/corpus_v2/CIR-2024-03.md
cdc6ccf247800f2d5147bc4e470c5ccb112a6c1fdf10e289c6152a816d6aba53  data/corpus_v2/CIR-2025-06.md
439b6f88e71cbc2a4df9c5d66f575e7aafce25561a5f2c07c141cf9d025cfb02  data/corpus_v2/CIR-2025-08-A.md
aa58fcb8516436363ff74ebc7c1fcedc4bab6e6624b47545c4694b3d36d9d9f0  data/corpus_v2/CIR-2025-08-B.md
275cca0ed3b6394cc1ccfcdb0c18e48af41f8fbeb7a0f544bdac3e0a9d6e24ec  data/corpus_v2/CIR-2025-10.md
1ca524a9a93ff210f116011fc277d1a4f998903df30d8e6da4c0823bd0da6348  data/corpus_v2/CIR-2026-01.md
50f72bfb34b1cec29c077720bd8e4041b60f6128a4b303d264cb9e61661f156d  data/corpus_v2/CIR-2026-02.md
4452933f0390802be6c0538e7731b202e1815e5e11e6e6caccadb7e9d32519d5  data/corpus_v2/CIR-2026-T6-CLAIM-A.md
c82aa16e347d5f7b9993163adc923f9ee446efc2874a8ad1c4dc93715a31e1c1  data/corpus_v2/CIR-2026-T6-CLAIM-B.md
49190fcae584f48a9b1a784a2aba46ca84dd8d2743e1813b9c2702599ef2b174  data/corpus_v2/CIR-2026-T6-COPAY-A.md
92b0f82c67e02ba9b7434ca04408ef7242ad956e92111133666319cc6bca7f3f  data/corpus_v2/CIR-2026-T6-COPAY-B.md
b4e075a8a4cb6f55fc88f1d38eac8e3e27f545b4b615cdb942e785711df8e35c  data/corpus_v2/CIR-2026-T6-GRV-A.md
0c2eb6b17a5bf03e61ed1bc9eb708c558ec2761ca5ca70cba674a4e151405418  data/corpus_v2/CIR-2026-T6-GRV-B.md
6a24dc470a9ac6a060f3cb596ac03ecec491615947d0054941a2ea16f09a1afe  data/corpus_v2/CIR-2026-T6-PREAUTH-A.md
754c257ea35de4808b0cf438988ab7053efa19f928279c29626e43943d1cbb76  data/corpus_v2/CIR-2026-T6-PREAUTH-B.md
42ffe0df51f9e5daa2070abdc1271165395020d910fba47de0107aa01c0d814f  data/corpus_v2/CIR-2026-T6-RENEW-A.md
4b51c1f8b81b0517ec24ab731018b93b822e9348865122f83745280edeba8c57  data/corpus_v2/CIR-2026-T6-RENEW-B.md
32597c88cdfbaa19d8bbde17bee35039d9e51837c302a2035f921321700c17df  data/corpus_v2/CIR-2026-T6-ROOM-A.md
5f656f873b355e6031590361505d3a043a5dab775b39c3c25a496eea9a492b92  data/corpus_v2/CIR-2026-T6-ROOM-B.md
fa23f31c5b19995a4977d70e5a8e884fac476daacc893e097825fe91d5d8cbe2  data/corpus_v2/FAQ-2024-01.md
a407a083166a8fbc59fc0d59885d0d8b95095be658dd0dd0aaffe1aa34a6298f  data/corpus_v2/FAQ-2024-02.md
0bf2c9954558259daa93d2cbc7cd8e3d2f2b0d9838aa2527fa7e2dd9fb1799d1  data/corpus_v2/FAQ-2025-01.md
c92683b49a84984ed794a04b0b1b7a95374cda01d89595237d00aa130be704a7  data/corpus_v2/FAQ-2025-06.md
f44463b12c9f517511c32f0dddc75eb05517d618ae49ecb2dcd30abc07c43ee1  data/corpus_v2/FAQ-2026-01.md
63916c84c3348d9f7cb59e4242c37bc04b17e9dfd7fc31b8d590b882e45e9429  data/corpus_v2/FAQ-2026-02.md
761818549eef8ae30bc81fcc9ec9dea73241b1abfb2d6aedb72173ef59e35a89  data/corpus_v2/MAN-2024-CLAIMS.md
5098c300c2f9a8ac8819328c07dad8758f4c35fb263912468adcf4fd476959b0  data/corpus_v2/MAN-2025-CASHLESS.md
389dab4c387222c5758d20704da98749e2da41d438010191e5db0a5697a357c6  data/corpus_v2/MAN-2025-CLAIMS.md
b864b8c672952e051ea3ce856b7db0e83e098853b03f5540481ced1a28919692  data/corpus_v2/MAN-2026-GRIEVANCE.md
a4cbff55fdd7623906eb5c0aea7dfdc2db1999c0d75e1a77a6d42363b7bb58f4  data/corpus_v2/NOTICE-2024-01.md
ef51cae29b45fdc80cd54f4c0967a7c0d09154b4ea0d2b6ccdf4b50c2c3035f2  data/corpus_v2/NOTICE-2025-02.md
c4f3ebbf71053a93cacbae76e117f131945a17c9fa68f19d972ca03763eeee89  data/corpus_v2/NOTICE-2025-11.md
0d6d2d82338f9f0fce2a5b834bed7d2c04aa68d5c86a31854cdd787806364c55  data/corpus_v2/NOTICE-2026-01.md
05c5af9a8ac6b43f5329c861983d40bb1c89e27ba99752d84a8b24304b0f6a47  data/corpus_v2/POL-2024-V1.md
f55b8f45f8a3dac1dc77377e91af0b10b741dc1e7d2f629c6ab1d9bce4bb92f1  data/corpus_v2/POL-2025-V2.md
0436bf1efac348445750d1aceb0288b45a6c3fcf8a1432859ef0ec267793fb97  data/corpus_v2/POL-2026-V3.md
dd9448779b66d91274235bbb6f75878a0b74a3c1e05a41da28e0481a53ef9937  data/corpus_v2/corpus_manifest.json
78649c14718200a2f9079cd398a2cd5801570984129a0cead6e5f4684a2dda3f  data/factsheet/aurelia_facts_v2.yaml
```
