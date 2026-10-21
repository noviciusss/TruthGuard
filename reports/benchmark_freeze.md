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

## Reproduce the hash check

```bash
sha256sum data/benchmark/questions.jsonl \
  data/benchmark/wild.jsonl data/benchmark/eval_subset_40.jsonl
```
