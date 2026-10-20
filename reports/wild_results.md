# Wild Robustness Evaluation

This report evaluates the 20 manually written questions in `data/benchmark/wild.jsonl` using the offline deterministic critic. It is separate from the frozen 140-question test result.

## Overall

- Questions scored: `20`
- Answer accuracy: `0.3500`
- Conflict F1: `0.4348`
- Resolution-mode accuracy: `0.3000`
- Provenance correctness: `0.9000`
- False-conflict rate: `0.1000`
- Abstention recall: `0.7500`

## By question type

| Type | Count | Answer accuracy | Conflict F1 | Mode accuracy | False-conflict rate |
|---|---:|---:|---:|---:|---:|
| T0 | 2 | 1.0000 | 0.0000 | 0.0000 | 1.0000 |
| T1 | 3 | 0.0000 | 0.5000 | 0.3333 | 0.0000 |
| T2 | 3 | 0.0000 | 0.5000 | 0.3333 | 0.0000 |
| T3 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| T4 | 3 | 0.3333 | 0.5000 | 0.3333 | 0.0000 |
| T5 | 3 | 1.0000 | 0.8000 | 0.6667 | 0.0000 |
| T6 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| T7 | 2 | 0.5000 | 0.0000 | 0.5000 | 0.0000 |

## Interpretation

The wild set tests indirect wording, multi-hop combinations, mixed topics, exceptions, unresolvable conflicts, no-conflict controls, and questions outside the corpus. These results are robustness evidence for the offline path, not additional official test-set performance.
