# Deterministic fact-level conflict fix

## Protocol

No API calls. Both phases use BGE Small + FAISS + BM25, offline
reformulations/synthesis, the same unchanged corpus/questions, and the
deterministic critic. Before evidence was captured before modifying detection.
Rules were selected on DEV and frozen before holdout reporting. TEST and wild
outcomes were not used to select thresholds or alter labels.

The threshold is structural: **two distinct documents**, a shared explicit
fact key, different fact-bound values, and positive evidence for the reported
type. No numeric similarity threshold was fitted to TEST. Only one candidate
rule set was selected, not a search over holdout outcomes.

## Change

The old critic collected every number in a topic-containing chunk. A renewal
passage could therefore appear to conflict because the same chunk contained a
claim deadline, age, date, or another benefit. Two unknown dates could also be
mistaken for an established same-date tie.

The new critic extracts individual fact lines or prose clauses, normalizes
durations, and excludes unrelated numbers. It requires:

- An applicable graph edge for T1.
- Explicit population/tier scopes for T2.
- Known differing dates for numeric/version T3/T4.
- Planned-care and notified emergency-exception evidence for T5.
- Known equal dates and authority for T6.

Otherwise it retains no conflict. Not-in-corpus remains a separate resolver
outcome when no answer is supported. Conflict positions cite the exact fact
line and character span rather than the entire mixed-fact chunk.

## DEV — rule selection only

40 DEV questions, including **2 T0 controls**:

| Phase | T0 false conflicts | T0 rate | Conflict F1 | Conflict recall | Mode accuracy | Answer proxy accuracy | T6/T7 abstention recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Before | 1/2 | 0.5000 | 0.8923 | 0.8286 | 0.8250 | 0.8500 | 1.0000 |
| After | 0/2 | 0.0000 | 0.9063 | 0.8286 | 0.8500 | 0.8500 | 1.0000 |

The DEV candidate removed the false positive without losing DEV conflict recall.

## TEST — frozen rule evaluation

All **140 TEST questions**, including **all 18 T0 controls**:

| Phase | T0 false conflicts | T0 rate | Conflict F1 | Conflict recall | Mode accuracy | Answer proxy accuracy | T6/T7 abstention recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Before | 15/18 | 0.8333 | 0.8134 | 0.7798 | 0.7214 | 0.8286 | 1.0000 |
| After | 0/18 | 0.0000 | 0.8763 | 0.7798 | 0.8214 | 0.8214 | 0.9677 |

The fix improves precision and mode accuracy, but **answer proxy accuracy
drops by 1/140** and abstention recall drops. No further rule selection was
done on these outcomes.

## Wild — separate robustness evidence

All **20 wild questions**, including **2 T0 controls**:

| Phase | T0 false conflicts | T0 rate | Conflict F1 | Conflict recall | Mode accuracy | Answer proxy accuracy | T6/T7 abstention recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Before | 2/2 | 1.0000 | 0.4800 | 0.3750 | 0.3500 | 0.4500 | 0.7500 |
| After | 0/2 | 0.0000 | 0.4762 | 0.3125 | 0.4000 | 0.4000 | 0.7500 |

Wild false positives disappear, but **conflict recall falls from 6/16 to 5/16
and answer proxy accuracy falls from 9/20 to 8/20**. This is a more conservative
detector, not a general robustness win. Zero observed false positives on two
controls does not establish a universally zero error rate.

## Limitations and evidence

Answer accuracy is the existing numeric/substring proxy, not semantic grading.
T6/T7 abstention recall is combined. Gold applicability/version-recovery issues
remain open in `reports/corpus_audit_programmatic.md`; the labels are unchanged.

```bash
TRUTHGUARD_OFFLINE=true PYTHONPATH=.:src .venv/bin/python scripts/evaluate_false_conflicts.py \
  --label current --output /tmp/truthguard-false-conflicts-current.json
```

Per-question evidence is committed in `reports/false_conflicts_before.json`,
`reports/false_conflicts_dev_selection.json`, and `reports/false_conflicts_after.json`.
Question-file SHA-256 hashes, conflict positions and span offsets are retained.
The before phase used the critic at commit `7ab4b48`; rerunning today's code
does not reproduce the old detector.
