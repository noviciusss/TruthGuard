# Wild Robustness Evaluation

This report evaluates the 20 manually written questions in `data/benchmark/wild.jsonl` using the offline deterministic critic. It is separate from the frozen 140-question test result.

## Overall comparison

| Backend | Questions | Answer accuracy | Conflict F1 | Mode accuracy | Provenance correctness | False-conflict rate | Abstention recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Hash embedder + BM25 | 20 | 0.3500 | 0.4348 | 0.3000 | 0.9000 | 0.1000 | 0.7500 |
| BGE small + FAISS + BM25 | 20 | 0.4500 | 0.4800 | 0.3500 | 0.9000 | 0.1000 | 0.7500 |

## BGE + FAISS failures by category

| Category | Question IDs |
|---|---|
| Retrieval miss | None in the BGE + FAISS run |
| Wrong conflict type | wild-001, wild-002, wild-003, wild-004, wild-005, wild-006, wild-007, wild-012, wild-018, wild-019 |
| Wrong mode | wild-001, wild-002, wild-003, wild-004, wild-005, wild-006, wild-007, wild-012, wild-013, wild-014, wild-015, wild-018, wild-019 |

The hash baseline retrieval misses were `wild-006` and `wild-011`. BGE + FAISS
removed those top-eight retrieval misses, but most remaining failures were
mode or conflict-type errors. The system therefore needs better conflict
reasoning and calibration for indirect/mixed-topic questions.

## Hash baseline by question type

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

The wild set tests indirect wording, multi-hop combinations, mixed topics, exceptions, unresolvable conflicts, no-conflict controls, and questions outside the corpus. The type table above is the hash baseline; the BGE aggregate row is the post-change result. These results are robustness evidence for the offline path, not additional official test-set performance.
