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

T0 scans lines containing the factsheet topic or bounded aliases (`renewal grace period`, `renewal may be completed`) and compares numeric durations only; unrelated durations do not count. For competition only, singular/plural and hyphenated durations such as `30-day` and `30 days` are treated alike. It cannot guarantee synonym completeness or adjudicate time/scope. T6 checks actual distinct annual-limit values, both issued/effective dates, and authority against loader and manifest. Its bounded topic aliases are `annual hospitalization limit` and `annual limit`; all matching positions are retained, including disagreements inside one document. The local tie does not prove whole-corpus abstention. Later higher-authority same-fact counterevidence fails current pair-only abstention. Gold was revised by explicit corpus adjudication; see `reports/gold_changes.md`. The audit performs no runtime tuning or benchmark freeze.

## Measured question counts

| Dataset | Rows | Pass | Fail | Unverifiable |
|---|---:|---:|---:|---:|
| questions.jsonl | 180 | 116 | 0 | 64 |
| wild.jsonl | 20 | 10 | 0 | 10 |
| eval_subset_40.jsonl | 40 | 26 | 0 | 14 |
| Unique (main + wild) | 200 | 126 | 0 | 74 |

## Per-type question counts

| Dataset | Type | Pass | Fail | Unverifiable |
|---|---|---:|---:|---:|
| questions.jsonl | T0 | 20 | 0 | 0 |
| questions.jsonl | T1 | 24 | 0 | 0 |
| questions.jsonl | T2 | 0 | 0 | 24 |
| questions.jsonl | T3 | 48 | 0 | 0 |
| questions.jsonl | T4 | 24 | 0 | 0 |
| questions.jsonl | T5 | 0 | 0 | 24 |
| questions.jsonl | T6 | 0 | 0 | 0 |
| questions.jsonl | T7 | 0 | 0 | 16 |
| wild.jsonl | T0 | 2 | 0 | 0 |
| wild.jsonl | T1 | 2 | 0 | 1 |
| wild.jsonl | T2 | 0 | 0 | 3 |
| wild.jsonl | T3 | 4 | 0 | 0 |
| wild.jsonl | T4 | 2 | 0 | 1 |
| wild.jsonl | T5 | 0 | 0 | 3 |
| wild.jsonl | T6 | 0 | 0 | 0 |
| wild.jsonl | T7 | 0 | 0 | 2 |
| eval_subset_40.jsonl | T0 | 2 | 0 | 0 |
| eval_subset_40.jsonl | T1 | 6 | 0 | 0 |
| eval_subset_40.jsonl | T2 | 0 | 0 | 6 |
| eval_subset_40.jsonl | T3 | 12 | 0 | 0 |
| eval_subset_40.jsonl | T4 | 6 | 0 | 0 |
| eval_subset_40.jsonl | T5 | 0 | 0 | 6 |
| eval_subset_40.jsonl | T6 | 0 | 0 | 0 |
| eval_subset_40.jsonl | T7 | 0 | 0 | 2 |
| Unique (main + wild) | T0 | 22 | 0 | 0 |
| Unique (main + wild) | T1 | 26 | 0 | 1 |
| Unique (main + wild) | T2 | 0 | 0 | 27 |
| Unique (main + wild) | T3 | 52 | 0 | 0 |
| Unique (main + wild) | T4 | 26 | 0 | 1 |
| Unique (main + wild) | T5 | 0 | 0 | 27 |
| Unique (main + wild) | T6 | 0 | 0 | 0 |
| Unique (main + wild) | T7 | 0 | 0 | 18 |

## Check counts and exact affected qids

### questions.jsonl

| Check | Pass | Fail | Unverifiable |
|---|---:|---:|---:|
| cited_sources | 180 | 0 | 0 |
| gold_value_presence | 116 | 0 | 48 |
| t0_same_fact_competition | 20 | 0 | 0 |
| t7_absence | 0 | 0 | 16 |
| t7_gold_shape | 16 | 0 | 0 |

**Exact fail qids (0):** none

**Exact unverifiable qids (64):** `t2-006`, `t5-017`, `t2-018`, `t7-001`, `t2-019`, `t7-005`, `t5-002`, `t2-009`, `t2-010`, `t2-014`, `t7-004`, `t5-022`, `t7-002`, `t5-021`, `t5-007`, `t2-012`, `t2-005`, `t5-019`, `t5-020`, `t2-002`, `t5-008`, `t2-024`, `t7-011`, `t2-004`, `t5-010`, `t7-006`, `t5-005`, `t2-022`, `t5-011`, `t2-016`, `t7-016`, `t5-015`, `t2-021`, `t5-003`, `t2-017`, `t5-018`, `t5-009`, `t5-024`, `t5-001`, `t7-013`, `t7-008`, `t2-020`, `t5-004`, `t7-015`, `t7-010`, `t5-023`, `t5-014`, `t7-009`, `t2-003`, `t2-023`, `t2-007`, `t2-013`, `t2-011`, `t7-012`, `t7-014`, `t7-007`, `t2-008`, `t5-013`, `t5-012`, `t5-016`, `t2-001`, `t7-003`, `t5-006`, `t2-015`

- **gold_value_presence:** Composed/paraphrased answer remains unverifiable even if a full string or all quantities occur. Qids: `t2-006`, `t5-017`, `t2-018`, `t2-019`, `t5-002`, `t2-009`, `t2-010`, `t2-014`, `t5-022`, `t5-021`, `t5-007`, `t2-012`, `t2-005`, `t5-019`, `t5-020`, `t2-002`, `t5-008`, `t2-024`, `t2-004`, `t5-010`, `t5-005`, `t2-022`, `t5-011`, `t2-016`, `t5-015`, `t2-021`, `t5-003`, `t2-017`, `t5-018`, `t5-009`, `t5-024`, `t5-001`, `t2-020`, `t5-004`, `t5-023`, `t5-014`, `t2-003`, `t2-023`, `t2-007`, `t2-013`, `t2-011`, `t2-008`, `t5-013`, `t5-012`, `t5-016`, `t2-001`, `t5-006`, `t2-015`

- **t7_absence:** No selected lexical probe hit; semantic absence is not provable by this scan. Qids: `t7-001`, `t7-005`, `t7-004`, `t7-002`, `t7-011`, `t7-006`, `t7-016`, `t7-013`, `t7-008`, `t7-015`, `t7-010`, `t7-009`, `t7-012`, `t7-014`, `t7-007`, `t7-003`
### wild.jsonl

| Check | Pass | Fail | Unverifiable |
|---|---:|---:|---:|
| cited_sources | 20 | 0 | 0 |
| gold_value_presence | 10 | 0 | 8 |
| t0_same_fact_competition | 2 | 0 | 0 |
| t7_absence | 0 | 0 | 2 |
| t7_gold_shape | 2 | 0 | 0 |

**Exact fail qids (0):** none

**Exact unverifiable qids (10):** `wild-003`, `wild-004`, `wild-009`, `wild-010`, `wild-015`, `wild-016`, `wild-017`, `wild-018`, `wild-019`, `wild-020`

- **gold_value_presence:** Composed/paraphrased answer remains unverifiable even if a full string or all quantities occur. Qids: `wild-003`, `wild-004`, `wild-009`, `wild-010`, `wild-017`, `wild-018`, `wild-019`, `wild-020`

- **t7_absence:** No selected lexical probe hit; semantic absence is not provable by this scan. Qids: `wild-015`, `wild-016`
### eval_subset_40.jsonl

| Check | Pass | Fail | Unverifiable |
|---|---:|---:|---:|
| cited_sources | 40 | 0 | 0 |
| gold_value_presence | 26 | 0 | 12 |
| subset_membership | 40 | 0 | 0 |
| t0_same_fact_competition | 2 | 0 | 0 |
| t7_absence | 0 | 0 | 2 |
| t7_gold_shape | 2 | 0 | 0 |

**Exact fail qids (0):** none

**Exact unverifiable qids (14):** `t2-002`, `t2-004`, `t2-005`, `t2-017`, `t2-022`, `t2-024`, `t5-001`, `t5-004`, `t5-005`, `t5-015`, `t5-016`, `t5-020`, `t7-007`, `t7-011`

- **gold_value_presence:** Composed/paraphrased answer remains unverifiable even if a full string or all quantities occur. Qids: `t2-002`, `t2-004`, `t2-005`, `t2-017`, `t2-022`, `t2-024`, `t5-001`, `t5-004`, `t5-005`, `t5-015`, `t5-016`, `t5-020`

- **t7_absence:** No selected lexical probe hit; semantic absence is not provable by this scan. Qids: `t7-007`, `t7-011`

## Metadata handling against manifest

All documents: `{'pass': 35, 'fail': 0, 'unverifiable': 0}`. Corrupted only: `{'pass': 14, 'fail': 0, 'unverifiable': 0}`.

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

Counts by document/fact/scope group: `{'pass': 53, 'fail': 0, 'unverifiable': 9}`.

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

## Input SHA-256 fingerprints

The companion JSON records every qid/check and all input hashes; hashes below make reruns auditable.

```text
dbe6c590a04f47740339f19c9af3c8714cbcdf37dd0b1d0899723de28e725bb5  config.yaml
ada05ac98bb86a016f29a3f9b08ba43898917517bdbdccc68d4fe345639de355  data/benchmark/eval_subset_40.jsonl
92b50347047535807d64b177ea3a90ca19a43937518f7f7e4305df86d146eafc  data/benchmark/questions.jsonl
5825609264492996b50656118fd218ac64461c00c3ebdf842ca6e9e01d920e8f  data/benchmark/wild.jsonl
35163301466f57a2ea7d85cb0c0f3aeab8a78e53ec524b6cf54b8a24bdfe5471  data/corpus/AMD-2025-03.md
4c4dc6c69468f1c76b511328fde9294fd9a56db8ad857dacb6d7cf5f6912ac43  data/corpus/AMD-2025-04.md
687a1f49a2c4c641f4e7703afa92ae0e1e7e9c68a0319a718fd39f8954b40010  data/corpus/AMD-2025-05.md
41d73ceb914c973f348167b22f8437b16b0a4bbfb14dd54312236a873f1cbe06  data/corpus/AMD-2025-07.md
7b3e40959566b2dfa2550fcde4b35cbf2ae40058fb77532a72de10a2f095dfab  data/corpus/AMD-2025-09.md
2ae6be528127234b8c26a195d0ddbe341b78d349e84187937e24cf7717c75843  data/corpus/AMD-2026-01.md
c22a4fab807b314c7e5bbd49607c1b63249613f29afe1ff3be03933db8c0e08c  data/corpus/AMD-2026-02.md
80dfb80a10516a53bd2d80f7f96c4f4c3cdf1307fb0086b114efb59fb619137a  data/corpus/AMD-2026-03.md
4df0be9cc81b1dd74e050cea56645b67b94841f6eb76463e39db3f64b1707e1f  data/corpus/AMD-2026-04.md
e2d9382a8c285395c0451468dbfac59040d82b0d913bf8a1494ac1d9c085a9b7  data/corpus/CIR-2024-01.md
b22f8862e8f53e9e02fd383931587e89d4a8dd40adc066e376eddf83ac73f02b  data/corpus/CIR-2024-02.md
db29d2c5d7fcd408efce1f8a0e23169e2a3345de4d3cec2480606b93e228c03a  data/corpus/CIR-2024-03.md
d197594ebdc28dc9749ca215c08d98df57415d50a635618e7d891737444ce161  data/corpus/CIR-2025-06.md
439b6f88e71cbc2a4df9c5d66f575e7aafce25561a5f2c07c141cf9d025cfb02  data/corpus/CIR-2025-08-A.md
aa58fcb8516436363ff74ebc7c1fcedc4bab6e6624b47545c4694b3d36d9d9f0  data/corpus/CIR-2025-08-B.md
275cca0ed3b6394cc1ccfcdb0c18e48af41f8fbeb7a0f544bdac3e0a9d6e24ec  data/corpus/CIR-2025-10.md
1ca524a9a93ff210f116011fc277d1a4f998903df30d8e6da4c0823bd0da6348  data/corpus/CIR-2026-01.md
d96631b99d55d820ba80f8dddcd3b4cf744b74353084a78eb2ea53090f0c476b  data/corpus/CIR-2026-02.md
fa23f31c5b19995a4977d70e5a8e884fac476daacc893e097825fe91d5d8cbe2  data/corpus/FAQ-2024-01.md
a407a083166a8fbc59fc0d59885d0d8b95095be658dd0dd0aaffe1aa34a6298f  data/corpus/FAQ-2024-02.md
0bf2c9954558259daa93d2cbc7cd8e3d2f2b0d9838aa2527fa7e2dd9fb1799d1  data/corpus/FAQ-2025-01.md
c92683b49a84984ed794a04b0b1b7a95374cda01d89595237d00aa130be704a7  data/corpus/FAQ-2025-06.md
e15f62cf82e7a8b0033e94e64d8b73a4afecb372c878922e9f9639644e630922  data/corpus/FAQ-2026-01.md
63916c84c3348d9f7cb59e4242c37bc04b17e9dfd7fc31b8d590b882e45e9429  data/corpus/FAQ-2026-02.md
761818549eef8ae30bc81fcc9ec9dea73241b1abfb2d6aedb72173ef59e35a89  data/corpus/MAN-2024-CLAIMS.md
5098c300c2f9a8ac8819328c07dad8758f4c35fb263912468adcf4fd476959b0  data/corpus/MAN-2025-CASHLESS.md
389dab4c387222c5758d20704da98749e2da41d438010191e5db0a5697a357c6  data/corpus/MAN-2025-CLAIMS.md
84d8ac7b5fdeb04924b48c36495b17c3adb1c96eb61e74a3bbfe96cd9ac3c9f9  data/corpus/MAN-2026-GRIEVANCE.md
a4cbff55fdd7623906eb5c0aea7dfdc2db1999c0d75e1a77a6d42363b7bb58f4  data/corpus/NOTICE-2024-01.md
ef51cae29b45fdc80cd54f4c0967a7c0d09154b4ea0d2b6ccdf4b50c2c3035f2  data/corpus/NOTICE-2025-02.md
c4f3ebbf71053a93cacbae76e117f131945a17c9fa68f19d972ca03763eeee89  data/corpus/NOTICE-2025-11.md
0d6d2d82338f9f0fce2a5b834bed7d2c04aa68d5c86a31854cdd787806364c55  data/corpus/NOTICE-2026-01.md
ef83398da17a240329432b16d6e71435222d3d30ef550d6eecb8d7020e1eff6d  data/corpus/POL-2024-V1.md
f55b8f45f8a3dac1dc77377e91af0b10b741dc1e7d2f629c6ab1d9bce4bb92f1  data/corpus/POL-2025-V2.md
0436bf1efac348445750d1aceb0288b45a6c3fcf8a1432859ef0ec267793fb97  data/corpus/POL-2026-V3.md
604321ab0e9875c8c73d103ad151274e330ce79e0d050f0310bdecff11c17b59  data/corpus/corpus_manifest.json
6986b15f32eb089e716ccd3374a5b0e4b0120fc6cc5881b532ee6e9360e447a9  data/factsheet/aurelia_facts.yaml
```
