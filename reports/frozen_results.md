# Frozen deterministic results

Run: 2026-10-21, after corpus/gold adjudication and benchmark freeze.

Provider/model: none; deterministic pipeline only. Retrieval: BGE Small +
FAISS + BM25. Reformulation: deterministic offline queries. No API calls.

## Frozen distributions and metrics

| Split | Questions | T0 | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T0 false conflicts | Conflict F1 | Answer proxy | Mode accuracy | Abstention recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DEV | 40 | 2 | 7 | 6 | 12 | 7 | 3 | 0 | 3 | 0/2 (0.0000) | 0.9063 | 0.7000 | 0.7000 | 1.0000 |
| TEST | 140 | 18 | 17 | 18 | 36 | 17 | 21 | 0 | 13 | 0/18 (0.0000) | 0.8763 | 0.7000 | 0.7000 | 1.0000 |
| wild | 20 | 2 | 3 | 3 | 4 | 3 | 3 | 0 | 2 | 0/2 (0.0000) | 0.5455 | 0.4000 | 0.4500 | 0.5000 |

The answer and mode metrics use the existing benchmark proxies. T6/T7 is no
longer a combined abstention category in the frozen benchmark because complete
corpus adjudication found no defensible current whole-corpus T6 examples.

## Before versus after the fact-level conflict fix

The pre-adjudication numbers are retained only as historical context and are
not directly comparable because 24 main T6 and 2 wild T6 gold labels were then
changed. The relevant result is the current frozen run above.

| Phase | TEST T0 false conflicts | TEST conflict F1 | TEST answer proxy | Wild T0 false conflicts | Wild conflict F1 | Wild answer proxy |
|---|---:|---:|---:|---:|---:|---:|
| Pre-adjudication historical fact-fix run | 0/18 after fix | 0.8763 | 0.8214 | 0/2 after fix | 0.4762 | 0.4000 |
| Frozen post-adjudication run | 0/18 | 0.8763 | 0.7000 | 0/2 | 0.5455 | 0.4000 |

The change in answer proxy is driven by gold-label adjudication, not attributed
to the conflict detector. The detailed pre-adjudication comparison remains in
`reports/false_conflicts.md`; `reports/gold_changes.md` lists every changed qid.

## Audit boundaries

- 0 TEST T6 questions remain; the requested target of 12 was impossible from
  existing evidence without fabricating ties or changing scope.
- Provenance remains document-level overlap/citation presence, not semantic
  support.
- Wild results remain weak and are not a production claim.
- No live model result is represented here.
