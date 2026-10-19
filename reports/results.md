# TruthGuard Evaluation Results

Updated: 2026-10-19

## Evaluation status

The TruthGuard test split has been run live with Groq for all 140 questions.
The live B0/B1/B2 baseline runs were not completed because the Groq free-tier
daily token budget was exhausted during the TruthGuard test run. The baseline
comparison below is therefore the complete offline deterministic-fallback
comparison, not a live-model comparison.

The corpus and benchmark remain fully synthetic. These results demonstrate
relative architecture behavior and are not production accuracy claims.

## Live TruthGuard test split

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

## Live development split

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
