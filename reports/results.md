# TruthGuard Evaluation Results

Updated: 2026-10-20

## Evaluation status

The TruthGuard test split has been run live with Groq synthesis and the
deterministic critic path for all 140 questions.
The live B0/B1/B2 baseline runs were not completed because the Groq free-tier
daily token budget was exhausted during the TruthGuard test run. The baseline
comparison below is therefore the complete offline deterministic-fallback
comparison, not a live-model comparison.

The corpus and benchmark remain fully synthetic. These results demonstrate
relative architecture behavior and are not production accuracy claims.

## Live TruthGuard test split — deterministic critic path

Split: 140 questions, generated from `data/benchmark/questions.jsonl`.

| Metric | Value | 95% bootstrap CI where applicable |
|---|---:|---:|
| Answer accuracy | 0.8286 | 0.7643–0.8857 |
| Conflict precision | 0.9043 | — |
| Conflict recall | 0.7798 | — |
| Conflict F1 | 0.8374 | — |
| Conflict type accuracy | 0.6071 | 0.5286–0.6857 |
| Resolution-mode accuracy | 0.7643 | 0.6929–0.8286 |
| Provenance correctness | 1.0000 | 1.0000–1.0000 |
| Unsupported-claim rate | 0.3082 | 0.2395–0.3782 |
| Blended-answer rate | 0.0000 | 0.0000–0.0000 |
| Abstention precision | 0.5636 | — |
| Abstention recall | 1.0000 | — |
| Abstention F1 | 0.7209 | — |
| False-conflict rate | 0.0643 | 0.0286–0.1071 |

Latency:

- Mean: approximately `9961.7 ms` per question.
- P95: approximately `16411.2 ms` per question.

The run is resumable in the local ignored file `reports/live_eval_test.jsonl`.
That file is intentionally not committed because it is generated runtime
output and may contain provider response material.

## Live development split — deterministic critic path

Split: 40 questions.

| Metric | Value | 95% bootstrap CI where applicable |
|---|---:|---:|
| Answer accuracy | 0.8500 | 0.7250–0.9500 |
| Conflict F1 | 0.8923 | — |
| Conflict type accuracy | 0.7250 | 0.5750–0.8500 |
| Resolution-mode accuracy | 0.8250 | 0.7000–0.9250 |
| Provenance correctness | 1.0000 | 1.0000–1.0000 |
| Unsupported-claim rate | 0.3271 | 0.2000–0.4625 |
| Blended-answer rate | 0.0000 | 0.0000–0.0000 |
| Abstention recall | 1.0000 | — |
| False-conflict rate | 0.0250 | 0.0000–0.0750 |

## Complete offline comparison

This comparison runs all four systems on the complete 140-question test split
using the deterministic offline dense-retrieval fallback and offline answer
path. It verifies the evaluation machinery and architecture behavior without
provider quota effects.

| System | Answer accuracy | Conflict F1 | Type accuracy | Resolution-mode accuracy |
|---|---:|---:|---:|---:|
| B0 Naive RAG | 0.7429 | 0.0000 | 0.0000 | 0.1286 |
| B1 Recency RAG | 0.7429 | 0.0000 | 0.0000 | 0.1286 |
| B2 Self-consistency | 0.7429 | 0.0000 | 0.0000 | 0.1286 |
| TruthGuard | 0.8286 | 0.8374 | 0.6071 | 0.7643 |

## Wild robustness set

The 20 manually written wild questions were evaluated separately with the
offline deterministic critic. Current results are intentionally reported as a
robustness gap rather than combined with the frozen test score:

| Metric | Value |
|---|---:|
| Answer accuracy | 0.3500 |
| Conflict F1 | 0.4348 |
| Resolution-mode accuracy | 0.3000 |
| Provenance correctness | 0.9000 |
| False-conflict rate | 0.1000 |
| Abstention recall | 0.7500 |

The indirect and mixed-topic wording is harder for the deterministic fallback
than the generated benchmark. The detailed breakdown is in
`reports/wild_results.md`; stronger query planning or a stable live critic is
needed before presenting this as a headline robustness result.

## Retrieval robustness: before and after BGE + FAISS

The development retrieval measurement uses 37 questions with gold source
documents. Recall@8 means that at least one gold source document appeared in
the top eight retrieved results. Wild evaluation uses the same offline
deterministic critic for both rows.

| Retrieval backend | Dev recall@8 | Wild answer accuracy | Wild conflict F1 | Wild mode accuracy | Wild false-conflict rate | Wild abstention recall |
|---|---:|---:|---:|---:|---:|---:|
| Hash embedder + BM25 | 1.0000 (37/37) | 0.3500 | 0.4348 | 0.3000 | 0.1000 | 0.7500 |
| BGE small + FAISS + BM25 | 1.0000 (37/37) | 0.4500 | 0.4800 | 0.3500 | 0.1000 | 0.7500 |

BGE + FAISS did not improve dev recall because the hash baseline already
retrieved at least one gold source for every eligible dev question. It improved
wild answer accuracy by 0.10 and conflict F1 by 0.0452, but the wild set
remains weak. The detailed per-question failure categories are in
`reports/wild_results.md`.

### Wild failure diagnosis

For the hash baseline, the retrieval misses were `wild-006` and `wild-011`.
After BGE + FAISS there were no top-eight retrieval misses. Remaining errors
were primarily wrong mode or wrong conflict type rather than pure retrieval
failure. This points to conflict reasoning and answer-mode calibration as the
next robustness target.

## Reproducibility and limitations

- All test/dev questions are synthetic and generated from the Aurelia Health
  ground-truth factsheet.
- The live Groq test used `openai/gpt-oss-120b` for configured Groq roles.
- Groq reported an 8,000-token/minute limit and a 200,000-token/day limit
  during the first account's run. The user supplied a new unused Groq account;
  the remaining 52 live test questions then completed successfully.
- Only Groq credentials are configured. Gemini/Mistral/OpenRouter fallback and
  live model-lineage-separated critic evaluation remain unverified.
- The current critic's deterministic path is what produced the final metrics;
  it is structured so the separate live critic provider can be enabled later.
- The optional BGE/FAISS CPU stack is isolated in `requirements-ml.txt`; the
  tested path uses a deterministic hash embedder to remain reproducible offline.
- Human verification of 30 benchmark questions is still required before
  presenting gold-label agreement as a result.
- Docker was not available in the current environment and remains unverified.
