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

The development measurement uses 37 questions with gold source documents.
Document recall@8 is the mean fraction of gold document IDs retrieved in the
top eight chunks. Any-source hit@8 is a weaker check: at least one gold document
appeared. Neither measures supporting-passage recall. Wild evaluation uses
the same offline deterministic critic and offline reformulations for both rows.
The cached live topic-plus-two-paraphrases call is implemented but **not used
in this before/after comparison**; its effect is still unmeasured.

| Retrieval backend | Dev document recall@8 | Dev any-source hit@8 | Wild answer accuracy | Wild conflict F1 | Wild mode accuracy | Wild false conflicts / all questions | Wild abstention recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Hash embedder + BM25 | 0.8243 | 1.0000 (37/37) | 0.3500 | 0.4348 | 0.3000 | 0.1000 | 0.7500 |
| BGE small + FAISS + BM25 | 0.8784 | 1.0000 (37/37) | 0.4500 | 0.4800 | 0.3500 | 0.1000 | 0.7500 |

BGE + FAISS improved dev document recall by 0.0541; the weaker any-source
hit rate was already saturated. Wild answer accuracy improved by 0.10 and
conflict F1 by 0.0452, but the wild set remains weak. The historical metric
`false_conflict` averages false conflicts over all questions; both wild T0
controls were falsely flagged, so the T0-only false-conflict rate is **2/2
(100%)**, not 10%. See `reports/wild_results.md` for per-question failures.

### Wild failure diagnosis

For the hash baseline, the retrieval misses were `wild-006` and `wild-011`.
After BGE + FAISS every source-labeled wild question retrieved at least one
gold document in the top eight. This does not establish that all competing
sources or supporting passages were retrieved. Ten conflict questions had no
detected conflict (not a wrong detected type); thirteen had the wrong mode.
The categories overlap. Improving conflict detection and mode selection is
still necessary; incomplete evidence retrieval has not been ruled out.

## Fixed 40-question test subset — incomplete live critic experiment

Subset: `data/benchmark/eval_subset_40.jsonl`, seed `20261020`, 6 each T1–T6,
2 T0, and 2 T7. These questions were selected once without inspecting outcomes;
the file is now committed. No prompts or gold labels were tuned on this subset.

The deterministic end-to-end BGE run completed 40/40. Its descriptive metrics
are conflict F1 `0.8824`, blended-answer proxy `0.0000`, T6/T7 combined abstention
recall `1.0000`, answer proxy accuracy `0.8500`. Both T0 controls were falsely
flagged: T0-only false-conflict rate `2/2 = 1.0000` (the legacy all-question
average is `0.0500`). Critic provider/model: **none, deterministic**.

The live Qwen experiment completed only 7/40 questions before rate-limit and
oversized-request failures. Eighteen questions recorded failures, and fifteen
were not reached before the shell timeout. **Do not compare these seven
successful answers to the 40-question deterministic aggregate.** Upstream
reformulation/synthesis also differ between the offline and live runs, so this
is not yet a controlled critic-only comparison.

Actual successful critic: `groq / qwen/qwen3.8-27b`. Actual successful
reformulation/synthesis: `groq / openai/gpt-oss-120b`. Mistral fallback attempts
failed and are not labeled as successful primary-model answers. The partial
call audit and remaining gaps are in `reports/critic_subset_status.md`.

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
