# Benchmark freeze

Freeze revision: 2026-10-21

The corpus/gold adjudication is complete for the approved decision. No
question labels, source passages, or subset membership may change after this
freeze without a new revision and a new report. The fixed subset retains its
original 40 qids/order; its labels are the frozen rows copied from the main
benchmark.

## Input hashes

| File | SHA-256 |
|---|---|
| `data/benchmark/questions.jsonl` | `92b50347047535807d64b177ea3a90ca19a43937518f7f7e4305df86d146eafc` |
| `data/benchmark/wild.jsonl` | `5825609264492996b50656118fd218ac64461c00c3ebdf842ca6e9e01d920e8f` |
| `data/benchmark/eval_subset_40.jsonl` | `ada05ac98bb86a016f29a3f9b08ba43898917517bdbdccc68d4fe345639de355` |

## Frozen distributions

- Main: 180 questions, 40 DEV and 140 TEST.
- Main TEST: T0=18, T1=24, T2=24, T3=48, T4=24, T5=24, T6=0, T7=16.
- Fixed subset: 40 TEST questions, T0=2, T1=6, T2=6, T3=12, T4=6,
  T5=6, T6=0, T7=2.
- Wild: 20 manually written questions; T6=0 after complete-corpus
  adjudication.

The requested minimum of 12 TEST T6 questions was not possible without
fabricating new same-date/same-authority ties or changing question scope. The
existing annual-limit tie is historical and the current whole-corpus winner is
`POL-2026-V3`; this limitation is recorded in `reports/gold_changes.md`.

The pre-adjudication 30-question review exporter cannot regenerate its old
4-T6 stratum because frozen TEST now contains zero T6 questions. The existing
sheet remains pre-freeze material; a new stratification requires human approval
and must not silently replace T6 with another type.

## Freeze v2 — additive genuine T6 revision

Freeze revision: 2026-10-21-v2

Freeze v2 is additive. The 180 v1 rows, including every existing question label,
remain unchanged as the prefix of `questions_v2.jsonl`; the v1 files and hashes
above remain the reference baseline. V2 adds 10 main rows (4 DEV T6 and 6 TEST
T6), 2 wild T6 rows, 12 new circular documents, and six new fact keys. Each v2
fact key has exactly two circulars with the same effective date, issued date,
authority rank, and scope; neither circular supersedes or amends the other, and
no third v2 document mentions the key.

### V2 input hashes

| File | SHA-256 |
|---|---|
| `data/factsheet/aurelia_facts_v2.yaml` | `78649c14718200a2f9079cd398a2cd5801570984129a0cead6e5f4684a2dda3f` |
| `data/corpus_v2/corpus_manifest.json` | `dd9448779b66d91274235bbb6f75878a0b74a3c1e05a41da28e0481a53ef9937` |
| `data/benchmark/questions_v2.jsonl` | `d0ffef1936bc9804a8359f456ed30c981d9e6baa6d7339505df8653ca744e87a` |
| `data/benchmark/wild_v2.jsonl` | `8e684bdefe8ba9f6b0309440fc7c1ec5a6e3180b06b4741fd22825752a42a1b8` |
| `data/benchmark/eval_subset_v2_40.jsonl` | `d7c23376f78bff192422c5b5fffb45bb123816962d2f377ef2f4033743cf9919` |

### V2 counts and distinct fact keys

| Dataset | Rows | T0 | T1 | T2 | T3 | T4 | T5 | T6 | T7 | Distinct fact keys |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Main DEV | 44 | 2 | 7 | 6 | 12 | 7 | 3 | 4 | 3 | 8 |
| Main TEST | 146 | 18 | 17 | 18 | 36 | 17 | 21 | 6 | 13 | 8 |
| Wild | 22 | 2 | 3 | 3 | 4 | 3 | 3 | 2 | 2 | 8 |
| Fixed v2 subset | 40 | 2 | 6 | 6 | 6 | 6 | 6 | 6 | 2 | 8 |

Distinct fact keys by type are reported in `reports/corpus_audit_v2.md` and
`reports/corpus_audit_v2.json`. V2 T6 uses six distinct keys:
`t6_room_rent_cap`, `t6_copay_rate`, `t6_grievance_response_window`,
`t6_claim_filing_deadline`, `t6_cashless_preauth_window`, and
`t6_renewal_grace_period`.

## Reproduce the hash check

```bash
sha256sum data/benchmark/questions.jsonl \
  data/benchmark/wild.jsonl data/benchmark/eval_subset_40.jsonl
```
