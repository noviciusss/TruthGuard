# Programmatic corpus audit (offline)

## Reproduce

```bash
TRUTHGUARD_OFFLINE=true .venv/bin/python scripts/audit_corpus_programmatic.py
TRUTHGUARD_OFFLINE=true .venv/bin/python -m pytest -q tests/test_programmatic_audit.py
make test
```

Default outputs: `reports/corpus_audit_programmatic.md` and `.json`. Use `--root`, `--output`, and `--json-output` to select paths. No network, API, retrieval, critic, model, or pipeline execution. Exit 0 means completion; `--fail-on-findings` exits 1 for any fail/unverifiable finding. Invalid inputs exit 2.

## Interpretation and limits

Pass means only the named mechanical check passed, never semantic gold correctness. Question rollup: any failure → fail; otherwise any unverifiable check → unverifiable; otherwise pass. Metadata recovery is counted separately, not folded into question gold counts. The fixed subset overlaps the main benchmark and is not additional unique evidence.

Value evidence is read from actual Markdown bodies/headings, not the factsheet, manifest answers, or runtime predictions. Matching is case/whitespace-normalized with word boundaries; raw case-sensitive hits are also recorded. Explicit section citations restrict matching to that section. Resolved answers must match the winner's cited evidence. Simple missing values fail. Nonliteral composed/paraphrased answers remain unverifiable even when quantities match; scenario arithmetic, exceptions, scope, and entailment require review. Literal claims and quantity matches are diagnostics in JSON, not substitute passes.

T7 searches every document with only the disclosed selected probe families. No hit is lexical evidence only and remains unverifiable; unknown subject families also remain unverifiable. A hit is a review candidate, not proof of coverage. Synonyms outside the probes, implicit statements, and semantic entailment are not detectable.

T0 scans lines containing the factsheet topic or bounded aliases (`renewal grace period`, `renewal may be completed`) and compares numeric durations only; unrelated durations do not count. For competition only, singular/plural and hyphenated durations such as `30-day` and `30 days` are treated alike. It cannot guarantee synonym completeness or adjudicate time/scope. T6 checks actual distinct annual-limit values, both issued/effective dates, and authority against loader and manifest. Its bounded topic aliases are `annual hospitalization limit` and `annual limit`; all matching positions are retained, including disagreements inside one document. The local tie does not prove whole-corpus abstention. No runtime was tuned on TEST and no gold was changed.

## Measured question counts

| Dataset | Rows | Pass | Fail | Unverifiable |
|---|---:|---:|---:|---:|
| questions.jsonl | 180 | 92 | 0 | 88 |
| wild.jsonl | 20 | 8 | 0 | 12 |
| eval_subset_40.jsonl | 40 | 20 | 0 | 20 |
| Unique (main + wild) | 200 | 100 | 0 | 100 |

## Check counts and exact affected qids

### questions.jsonl

| Check | Pass | Fail | Unverifiable |
|---|---:|---:|---:|
| cited_sources | 180 | 0 | 0 |
| gold_value_presence | 92 | 0 | 48 |
| t0_same_fact_competition | 20 | 0 | 0 |
| t6_global_abstention | 0 | 0 | 24 |
| t6_gold_shape | 24 | 0 | 0 |
| t6_pair | 24 | 0 | 0 |
| t7_absence | 0 | 0 | 16 |
| t7_gold_shape | 16 | 0 | 0 |

**Exact fail qids (0):** none

**Exact unverifiable qids (88):** `t2-006`, `t5-017`, `t2-018`, `t6-020`, `t7-001`, `t2-019`, `t6-005`, `t7-005`, `t6-013`, `t6-003`, `t6-011`, `t5-002`, `t2-009`, `t2-010`, `t2-014`, `t7-004`, `t5-022`, `t6-015`, `t6-014`, `t7-002`, `t6-017`, `t6-016`, `t5-021`, `t5-007`, `t2-012`, `t2-005`, `t5-019`, `t5-020`, `t2-002`, `t5-008`, `t2-024`, `t6-021`, `t7-011`, `t2-004`, `t5-010`, `t7-006`, `t5-005`, `t2-022`, `t6-007`, `t5-011`, `t2-016`, `t7-016`, `t6-004`, `t6-006`, `t5-015`, `t2-021`, `t5-003`, `t2-017`, `t5-018`, `t5-009`, `t5-024`, `t6-009`, `t5-001`, `t6-012`, `t7-013`, `t7-008`, `t2-020`, `t6-002`, `t6-001`, `t5-004`, `t7-015`, `t7-010`, `t5-023`, `t6-024`, `t5-014`, `t6-008`, `t7-009`, `t2-003`, `t2-023`, `t2-007`, `t6-019`, `t2-013`, `t2-011`, `t6-023`, `t7-012`, `t7-014`, `t7-007`, `t2-008`, `t5-013`, `t6-022`, `t5-012`, `t5-016`, `t6-010`, `t2-001`, `t6-018`, `t7-003`, `t5-006`, `t2-015`

- **gold_value_presence:** Composed/paraphrased answer is not a literal string; atom hits do not prove its semantics. Qids: `t2-006`, `t5-017`, `t2-018`, `t2-019`, `t5-002`, `t2-009`, `t2-010`, `t2-014`, `t5-022`, `t5-021`, `t5-007`, `t2-012`, `t2-005`, `t5-019`, `t5-020`, `t2-002`, `t5-008`, `t2-024`, `t2-004`, `t5-010`, `t5-005`, `t2-022`, `t5-011`, `t2-016`, `t5-015`, `t2-021`, `t5-003`, `t2-017`, `t5-018`, `t5-009`, `t5-024`, `t5-001`, `t2-020`, `t5-004`, `t5-023`, `t5-014`, `t2-003`, `t2-023`, `t2-007`, `t2-013`, `t2-011`, `t2-008`, `t5-013`, `t5-012`, `t5-016`, `t2-001`, `t5-006`, `t2-015`

- **t6_global_abstention:** Pair tie alone cannot establish global abstention; review other same-fact documents and applicability. Qids: `t6-020`, `t6-005`, `t6-013`, `t6-003`, `t6-011`, `t6-015`, `t6-014`, `t6-017`, `t6-016`, `t6-021`, `t6-007`, `t6-004`, `t6-006`, `t6-009`, `t6-012`, `t6-002`, `t6-001`, `t6-024`, `t6-008`, `t6-019`, `t6-023`, `t6-022`, `t6-010`, `t6-018`

- **t7_absence:** No selected lexical probe hit; semantic absence is not provable by this scan. Qids: `t7-001`, `t7-005`, `t7-004`, `t7-002`, `t7-011`, `t7-006`, `t7-016`, `t7-013`, `t7-008`, `t7-015`, `t7-010`, `t7-009`, `t7-012`, `t7-014`, `t7-007`, `t7-003`
### wild.jsonl

| Check | Pass | Fail | Unverifiable |
|---|---:|---:|---:|
| cited_sources | 20 | 0 | 0 |
| gold_value_presence | 8 | 0 | 8 |
| t0_same_fact_competition | 2 | 0 | 0 |
| t6_global_abstention | 0 | 0 | 2 |
| t6_gold_shape | 2 | 0 | 0 |
| t6_pair | 2 | 0 | 0 |
| t7_absence | 0 | 0 | 2 |
| t7_gold_shape | 2 | 0 | 0 |

**Exact fail qids (0):** none

**Exact unverifiable qids (12):** `wild-003`, `wild-004`, `wild-009`, `wild-010`, `wild-011`, `wild-012`, `wild-015`, `wild-016`, `wild-017`, `wild-018`, `wild-019`, `wild-020`

- **gold_value_presence:** Composed/paraphrased answer is not a literal string; atom hits do not prove its semantics. Qids: `wild-003`, `wild-004`, `wild-009`, `wild-010`, `wild-017`, `wild-018`, `wild-019`, `wild-020`

- **t6_global_abstention:** Pair tie alone cannot establish global abstention; review other same-fact documents and applicability. Qids: `wild-011`, `wild-012`

- **t7_absence:** No selected lexical probe hit; semantic absence is not provable by this scan. Qids: `wild-015`, `wild-016`
### eval_subset_40.jsonl

| Check | Pass | Fail | Unverifiable |
|---|---:|---:|---:|
| cited_sources | 40 | 0 | 0 |
| gold_value_presence | 20 | 0 | 12 |
| subset_membership | 40 | 0 | 0 |
| t0_same_fact_competition | 2 | 0 | 0 |
| t6_global_abstention | 0 | 0 | 6 |
| t6_gold_shape | 6 | 0 | 0 |
| t6_pair | 6 | 0 | 0 |
| t7_absence | 0 | 0 | 2 |
| t7_gold_shape | 2 | 0 | 0 |

**Exact fail qids (0):** none

**Exact unverifiable qids (20):** `t2-002`, `t2-004`, `t2-005`, `t2-017`, `t2-022`, `t2-024`, `t5-001`, `t5-004`, `t5-005`, `t5-015`, `t5-016`, `t5-020`, `t6-001`, `t6-008`, `t6-016`, `t6-018`, `t6-021`, `t6-023`, `t7-007`, `t7-011`

- **gold_value_presence:** Composed/paraphrased answer is not a literal string; atom hits do not prove its semantics. Qids: `t2-002`, `t2-004`, `t2-005`, `t2-017`, `t2-022`, `t2-024`, `t5-001`, `t5-004`, `t5-005`, `t5-015`, `t5-016`, `t5-020`

- **t6_global_abstention:** Pair tie alone cannot establish global abstention; review other same-fact documents and applicability. Qids: `t6-001`, `t6-008`, `t6-016`, `t6-018`, `t6-021`, `t6-023`

- **t7_absence:** No selected lexical probe hit; semantic absence is not provable by this scan. Qids: `t7-007`, `t7-011`

## Metadata recovery against manifest

All documents: `{'pass': 28, 'fail': 7, 'unverifiable': 0}`. Corrupted only: `{'pass': 7, 'fail': 7, 'unverifiable': 0}`.

Compared identity, title, type, version, issued/effective dates, authority, supersedes, and amends. Derived metadata_source/confidence are disclosed in JSON but not expected to equal generator annotations.

| Document | Corruption | Result | Physical-field differences |
|---|---|---|---|
| POL-2024-V1 | missing_effective | pass | `{}` |
| POL-2025-V2 | wrong_version | fail | `{"version": {"expected": "2.0", "loaded": "0.0"}}` |
| POL-2026-V3 | none | pass | `{}` |
| AMD-2025-03 | none | pass | `{}` |
| AMD-2025-04 | none | pass | `{}` |
| AMD-2025-05 | missing_effective | pass | `{}` |
| AMD-2025-07 | wrong_version | fail | `{"version": {"expected": "2025-07", "loaded": "0.0"}}` |
| AMD-2025-09 | none | pass | `{}` |
| AMD-2026-01 | none | pass | `{}` |
| AMD-2026-02 | none | pass | `{}` |
| AMD-2026-03 | missing_effective | pass | `{}` |
| AMD-2026-04 | wrong_version | fail | `{"version": {"expected": "2026-04", "loaded": "0.0"}}` |
| CIR-2024-01 | none | pass | `{}` |
| CIR-2024-02 | none | pass | `{}` |
| CIR-2024-03 | none | pass | `{}` |
| CIR-2025-06 | missing_effective | pass | `{}` |
| CIR-2025-08-A | wrong_version | fail | `{"version": {"expected": "2025/08-A", "loaded": "0.0"}}` |
| CIR-2025-08-B | none | pass | `{}` |
| CIR-2025-10 | none | pass | `{}` |
| CIR-2026-01 | none | pass | `{}` |
| CIR-2026-02 | missing_effective | pass | `{}` |
| FAQ-2024-01 | wrong_version | fail | `{"version": {"expected": "2024.1", "loaded": "0.0"}}` |
| FAQ-2024-02 | none | pass | `{}` |
| FAQ-2025-01 | none | pass | `{}` |
| FAQ-2025-06 | none | pass | `{}` |
| FAQ-2026-01 | missing_effective | pass | `{}` |
| FAQ-2026-02 | wrong_version | fail | `{"version": {"expected": "2026.2", "loaded": "0.0"}}` |
| MAN-2024-CLAIMS | none | pass | `{}` |
| MAN-2025-CLAIMS | none | pass | `{}` |
| MAN-2025-CASHLESS | none | pass | `{}` |
| MAN-2026-GRIEVANCE | missing_effective | pass | `{}` |
| NOTICE-2024-01 | wrong_version | fail | `{"version": {"expected": "2024/01", "loaded": "0.0"}}` |
| NOTICE-2025-02 | none | pass | `{}` |
| NOTICE-2025-11 | none | pass | `{}` |
| NOTICE-2026-01 | none | pass | `{}` |

### Exact qids citing failed metadata documents

These are metadata-impact qids, separate from question gold failures above.

- `POL-2025-V2` / `questions.jsonl`: `t5-017`, `t5-002`, `t5-022`, `t5-021`, `t5-007`, `t5-019`, `t5-020`, `t5-008`, `t5-010`, `t5-005`, `t5-011`, `t5-015`, `t5-003`, `t5-018`, `t5-009`, `t5-024`, `t5-001`, `t5-004`, `t5-023`, `t5-014`, `t5-013`, `t5-012`, `t5-016`, `t5-006`
- `POL-2025-V2` / `wild.jsonl`: `wild-009`, `wild-010`, `wild-018`
- `POL-2025-V2` / `eval_subset_40.jsonl`: `t5-001`, `t5-004`, `t5-005`, `t5-015`, `t5-016`, `t5-020`
- `AMD-2025-07` / `questions.jsonl`: none
- `AMD-2025-07` / `wild.jsonl`: none
- `AMD-2025-07` / `eval_subset_40.jsonl`: none
- `AMD-2026-04` / `questions.jsonl`: none
- `AMD-2026-04` / `wild.jsonl`: none
- `AMD-2026-04` / `eval_subset_40.jsonl`: none
- `CIR-2025-08-A` / `questions.jsonl`: `t6-020`, `t6-005`, `t6-013`, `t6-003`, `t6-011`, `t6-015`, `t6-014`, `t6-017`, `t6-016`, `t6-021`, `t6-007`, `t6-004`, `t6-006`, `t6-009`, `t6-012`, `t6-002`, `t6-001`, `t6-024`, `t6-008`, `t6-019`, `t6-023`, `t6-022`, `t6-010`, `t6-018`
- `CIR-2025-08-A` / `wild.jsonl`: `wild-011`, `wild-012`
- `CIR-2025-08-A` / `eval_subset_40.jsonl`: `t6-001`, `t6-008`, `t6-016`, `t6-018`, `t6-021`, `t6-023`
- `FAQ-2024-01` / `questions.jsonl`: none
- `FAQ-2024-01` / `wild.jsonl`: none
- `FAQ-2024-01` / `eval_subset_40.jsonl`: none
- `FAQ-2026-02` / `questions.jsonl`: none
- `FAQ-2026-02` / `wild.jsonl`: none
- `FAQ-2026-02` / `eval_subset_40.jsonl`: none
- `NOTICE-2024-01` / `questions.jsonl`: none
- `NOTICE-2024-01` / `wild.jsonl`: none
- `NOTICE-2024-01` / `eval_subset_40.jsonl`: none

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

## Evidence and human decisions

1. **Composed gold:** review all `gold_value_presence` unverifiable qids listed above. Check clauses, scope, exception, and scenario arithmetic against the exact cited sections in JSON. Safe proposal: add independently reviewed atomic evidence mappings or correct a section citation if it points to the wrong passage. Approval is needed for any answer/claim/status change. Missing full strings must not be relabeled as literal passes.

2. **T6 global applicability:** decide whether questions are deliberately restricted to the two August circulars or ask for a current whole-corpus answer. Inspect all `other_positions` in JSON, particularly later/higher-authority material if present. Possible safe proposals, requiring owner approval: explicitly restrict the question to the cited documents, or semantically revise gold after adjudication. Do not infer a winner automatically from the pair tie or a later date alone.

3. **Metadata:** failed version recovery means the current loader retained a physical value that differs from the manifest. A safe future fix would flag an unsupported version as unknown or recover it only from an independently documented rule/body cue, with tests. Do not silently copy manifest gold into runtime metadata. Owner approval/clarification is needed for the recovery rule.

4. **T7:** a human must adjudicate semantic absence for every T7 qid; the lexical no-hit result is insufficient. T0 passes are bounded topic/alias scans, not a proof that no paraphrased competing rule exists.

5. **Internal annual-limit contradictions:** the audit retains both prose and operational-rule positions rather than selecting one. For each document listed below, clarify the intended value before approving any corpus/factsheet/gold edit. A safe proposed repair is to make its prose and operational rule agree on the independently adjudicated value, then re-audit affected T6 gold; this audit does not perform that repair.

### Internal annual-limit disagreements and exact affected qids

- `questions.jsonl`: `NOTICE-2025-11` contains `('500000', '600000')`; review `t6-020`, `t6-005`, `t6-013`, `t6-003`, `t6-011`, `t6-015`, `t6-014`, `t6-017`, `t6-016`, `t6-021`, `t6-007`, `t6-004`, `t6-006`, `t6-009`, `t6-012`, `t6-002`, `t6-001`, `t6-024`, `t6-008`, `t6-019`, `t6-023`, `t6-022`, `t6-010`, `t6-018`
- `wild.jsonl`: `NOTICE-2025-11` contains `('500000', '600000')`; review `wild-011`, `wild-012`
- `eval_subset_40.jsonl`: `NOTICE-2025-11` contains `('500000', '600000')`; review `t6-001`, `t6-008`, `t6-016`, `t6-018`, `t6-021`, `t6-023`

### T0 and T6 actual corpus positions

- Pair `CIR-2025-08-A` / `CIR-2025-08-B`: values `[['500000 currency units'], ['600000 currency units']]`, effective `['2025-08-01', '2025-08-01']`, issued `['2025-08-01', '2025-08-01']`, authority `[2, 2]`; loaded tie `True`, manifest tie `True`, loaded agrees with manifest `True`.
- `NOTICE-2025-11:17` (effective 2025-11-01, issued 2025-11-01, authority 3): The filed Standard plan annual limit is 500000 currency units.
- `NOTICE-2025-11:21` (effective 2025-11-01, issued 2025-11-01, authority 3): - **annual hospitalization limit** (Aurelia Standard plan): 600000 currency units per policy year.
- `POL-2026-V3:27` (effective 2026-01-01, issued 2025-12-01, authority 4): - **annual hospitalization limit** (Aurelia Standard plan): 600000 currency units per policy year.
- `CIR-2024-01:17` (effective 2024-02-01, issued 2024-01-20, authority 2): A renewal may be completed within 30 days after the due date.
- `CIR-2024-01:21` (effective 2024-02-01, issued 2024-01-20, authority 2): - **renewal grace period** (all active plans): 30 days after renewal due date.
- `CIR-2025-10:17` (effective 2025-10-01, issued 2025-09-15, authority 2): The 30-day renewal grace period applies to all active plans.
- `CIR-2025-10:21` (effective 2025-10-01, issued 2025-09-15, authority 2): - **renewal grace period** (all active plans): 30 days after renewal due date.
- `FAQ-2026-01:17` (effective 2026-01-20, issued 2026-01-20, authority 0): Members have a 30-day renewal grace period.
- `FAQ-2026-01:21` (effective 2026-01-20, issued 2026-01-20, authority 0): - **renewal grace period** (all active plans): 30 days after renewal due date.
- `POL-2026-V3:25` (effective 2026-01-01, issued 2025-12-01, authority 4): - **renewal grace period** (all active plans): 30 days after renewal due date.
- Pair `CIR-2025-08-A` / `NOTICE-2025-11`: values `[['500000 currency units'], ['500000 currency units', '600000 currency units']]`, effective `['2025-08-01', '2025-11-01']`, issued `['2025-08-01', '2025-11-01']`, authority `[2, 3]`; loaded tie `False`, manifest tie `False`, loaded agrees with manifest `True`.
- Pair `CIR-2025-08-B` / `NOTICE-2025-11`: values `[['600000 currency units'], ['500000 currency units', '600000 currency units']]`, effective `['2025-08-01', '2025-11-01']`, issued `['2025-08-01', '2025-11-01']`, authority `[2, 3]`; loaded tie `False`, manifest tie `False`, loaded agrees with manifest `True`.

## Input SHA-256 fingerprints

The companion JSON records every qid/check and all input hashes; hashes below make reruns auditable.

```text
9501b029675e9ada7b3267d10f5caa8300b5037a59ab75b3c4484dce71ab1e8f  config.yaml
727c47baae44aa0505d2902c1841bfd9fc77c094ce485bf0786d752328b233a7  data/benchmark/eval_subset_40.jsonl
f87ca78ef04bac3a8ecc82f72c545f752dab52799457fbe877f4569848c2c4fd  data/benchmark/questions.jsonl
4f898d53a48d8810aab75d367c527b8ebd950e00cf11d952579d0d93ef97598f  data/benchmark/wild.jsonl
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
34fc4bc002e29912bd4552d06c20b226a7566c2e4f9552f9a48cb590a7fcb8fb  data/corpus/CIR-2024-03.md
d197594ebdc28dc9749ca215c08d98df57415d50a635618e7d891737444ce161  data/corpus/CIR-2025-06.md
439b6f88e71cbc2a4df9c5d66f575e7aafce25561a5f2c07c141cf9d025cfb02  data/corpus/CIR-2025-08-A.md
aa58fcb8516436363ff74ebc7c1fcedc4bab6e6624b47545c4694b3d36d9d9f0  data/corpus/CIR-2025-08-B.md
275cca0ed3b6394cc1ccfcdb0c18e48af41f8fbeb7a0f544bdac3e0a9d6e24ec  data/corpus/CIR-2025-10.md
1ca524a9a93ff210f116011fc277d1a4f998903df30d8e6da4c0823bd0da6348  data/corpus/CIR-2026-01.md
d96631b99d55d820ba80f8dddcd3b4cf744b74353084a78eb2ea53090f0c476b  data/corpus/CIR-2026-02.md
fa23f31c5b19995a4977d70e5a8e884fac476daacc893e097825fe91d5d8cbe2  data/corpus/FAQ-2024-01.md
a407a083166a8fbc59fc0d59885d0d8b95095be658dd0dd0aaffe1aa34a6298f  data/corpus/FAQ-2024-02.md
00ace05405d962ea209c361c6c370a124e0b5665c2aab311bc82036b592f5874  data/corpus/FAQ-2025-01.md
c92683b49a84984ed794a04b0b1b7a95374cda01d89595237d00aa130be704a7  data/corpus/FAQ-2025-06.md
e15f62cf82e7a8b0033e94e64d8b73a4afecb372c878922e9f9639644e630922  data/corpus/FAQ-2026-01.md
63916c84c3348d9f7cb59e4242c37bc04b17e9dfd7fc31b8d590b882e45e9429  data/corpus/FAQ-2026-02.md
761818549eef8ae30bc81fcc9ec9dea73241b1abfb2d6aedb72173ef59e35a89  data/corpus/MAN-2024-CLAIMS.md
5098c300c2f9a8ac8819328c07dad8758f4c35fb263912468adcf4fd476959b0  data/corpus/MAN-2025-CASHLESS.md
389dab4c387222c5758d20704da98749e2da41d438010191e5db0a5697a357c6  data/corpus/MAN-2025-CLAIMS.md
84d8ac7b5fdeb04924b48c36495b17c3adb1c96eb61e74a3bbfe96cd9ac3c9f9  data/corpus/MAN-2026-GRIEVANCE.md
a4cbff55fdd7623906eb5c0aea7dfdc2db1999c0d75e1a77a6d42363b7bb58f4  data/corpus/NOTICE-2024-01.md
ef51cae29b45fdc80cd54f4c0967a7c0d09154b4ea0d2b6ccdf4b50c2c3035f2  data/corpus/NOTICE-2025-02.md
b2fda79a89835dd4f423649c81baf395fe4c074532b29955a5d82abae560de4d  data/corpus/NOTICE-2025-11.md
0d6d2d82338f9f0fce2a5b834bed7d2c04aa68d5c86a31854cdd787806364c55  data/corpus/NOTICE-2026-01.md
ef83398da17a240329432b16d6e71435222d3d30ef550d6eecb8d7020e1eff6d  data/corpus/POL-2024-V1.md
f55b8f45f8a3dac1dc77377e91af0b10b741dc1e7d2f629c6ab1d9bce4bb92f1  data/corpus/POL-2025-V2.md
0436bf1efac348445750d1aceb0288b45a6c3fcf8a1432859ef0ec267793fb97  data/corpus/POL-2026-V3.md
c9886f0a736a04dad5ed49fc178b3d3fec2075dda4118bb068a4a84478d196df  data/corpus/corpus_manifest.json
2d07aca3342b1e7d8ea3f5413041dc5405d41590d08a50e87b178cb62cccc350  data/factsheet/aurelia_facts.yaml
```
