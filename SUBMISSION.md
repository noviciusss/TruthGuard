# TruthGuard Hackathon Submission

## One-line pitch

TruthGuard is an auditable RAG system that detects contradictory documents,
explains which source should be trusted, and abstains instead of silently
blending incompatible answers.

## The problem

Most retrieval-augmented generation systems assume that retrieved passages are
mutually compatible. In policy, legal, compliance, and operations corpora, that
assumption is unsafe: an old policy can conflict with a later amendment, an
exception can apply to a narrower scope, or two equally authoritative
documents can remain irreconcilable.

A fluent answer can therefore be wrong while looking well supported.

## The solution

TruthGuard turns disagreement into an explicit reasoning step:

1. Retrieve relevant passages with hybrid search.
2. Search toward amendments, exceptions, and related graph neighbors.
3. Draft an answer using only retrieved evidence.
4. Decompose the draft into atomic claims.
5. Verify each claim against all retrieved passages.
6. Detect and classify conflicts as T0–T7.
7. Follow supersession and amendment relationships.
8. Calculate transparent trust factors.
9. Resolve, answer conditionally, abstain, or report that the topic is absent.
10. Show citations, conflict positions, trust scores, and the execution trace.

## What makes it different

### Conflict-aware rather than blend-oriented

TruthGuard does not treat the top retrieved passage as automatically correct.
It searches for competing positions and retains the disagreement in the final
answer.

### Claim-level provenance

The system maps claims to exact corpus chunks and character spans, so a judge
can inspect the evidence behind an answer.

### Calibrated abstention

For same-date, same-authority disagreements, TruthGuard does not invent a
winner. It returns an abstention with the competing positions.

### Lineage separation

The intended live architecture uses Groq for synthesis and Gemini for the
critic, with Mistral as a fallback. The complete benchmark metrics currently
use the deterministic critic path; the live Gemini smoke is a separate
validation item.

## Architecture

```text
Question
   ↓
Hybrid BM25 + dense retrieval
   ↓
Conflict-seeking reformulations + graph neighbors
   ↓
Passage-only synthesizer
   ↓
Claim decomposition and evidence verification
   ↓
Pairwise conflict scan and T1–T6 typing
   ↓
Self-critique of proposed conflicts
   ↓
Trust scoring: recency, authority, specificity,
               corroboration, metadata confidence
   ↓
Resolver
   ↓
Resolved / conditional / abstained / not-in-corpus answer
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the detailed
component-by-component explanation.

## Dataset and benchmark

- Fully synthetic Aurelia Health corpus.
- 35 policy, amendment, circular, FAQ, manual, and notice documents.
- 14 ground-truth facts.
- 40% intentionally incomplete or corrupted header metadata.
- 180 benchmark questions.
- 40 development questions.
- 140 frozen test questions.
- T0 controls for no-conflict behavior.
- T1–T6 conflict categories.
- T7 not-in-corpus questions.
- 20 manually written wild robustness questions.

The synthetic corpus avoids private health data while preserving the reasoning
challenge of contradictory policy documents.

The wild set can be evaluated offline with `make wild`; its report is kept
separate from the official frozen test result.

## Current results

The final live TruthGuard test split completed all 140 questions:

| Metric | Result |
|---|---:|
| Answer accuracy | 0.8286 |
| Conflict F1 | 0.8374 |
| Conflict type accuracy | 0.6071 |
| Resolution-mode accuracy | 0.7643 |
| Provenance correctness | 1.0000 |
| Blended-answer rate | 0.0000 |
| Abstention recall | 1.0000 |

These are architecture results on a synthetic benchmark, not production
accuracy claims. They were generated using the deterministic critic path. The
live Gemini critic is implemented and has a bounded smoke test, but provider
availability has not yet been stable enough to replace the benchmark metrics
with a Gemini-critic run.

The complete table, offline comparisons, latency, confidence intervals, and
limitations are in [`reports/results.md`](reports/results.md).

Wild robustness results are in [`reports/wild_results.md`](reports/wild_results.md)
when generated with `make wild`. The current offline result is intentionally
reported as a weakness: answer accuracy is `0.3500` and conflict F1 is
`0.4348` on indirect/mixed-topic wording. This shows where a stronger live
critic or improved query planning is still needed.

## Reproduce the demo

### Offline judge demo

```bash
make install
make test
make demo
```

The demo writes `reports/demo_output.md` and covers supersession, scope,
numeric change, exception handling, unresolvable conflict, and not-in-corpus
behavior.

### Streamlit UI

```bash
make ui
```

Open `http://127.0.0.1:8501`.

### FastAPI API

```bash
make api
```

Open `http://127.0.0.1:8000/docs`.

### Offline evaluation

```bash
PYTHONPATH=src .venv/bin/python -m bench.run_eval \
  --questions data/benchmark/questions.jsonl \
  --output /tmp/truthguard-offline.jsonl \
  --system truthguard \
  --split test \
  --no-llm-critic
```

## Live provider mode

Set `TRUTHGUARD_OFFLINE=false` and provide keys in `.env`. Start with a small
bounded run because free-tier quotas are enforced by the router:

```bash
PYTHONPATH=src .venv/bin/python -m bench.run_eval \
  --questions data/benchmark/questions.jsonl \
  --output reports/live_eval_dev.jsonl \
  --system truthguard \
  --split dev \
  --limit 5
```

The router records provider, model, cache, latency, fallback, and budget data.
Do not present a fallback provider as evidence for the intended Gemini critic
lineage.

## Known limitations

1. The corpus is synthetic and intentionally small.
2. The 30-question human review is prepared but still requires reviewer input.
3. The independent second-LLM corpus audit remains pending.
4. Live B0/B1/B2 baseline comparison remains pending.
5. The Gemini critic has been implemented, but free-tier availability has been
   intermittent during smoke validation.
6. Docker is documented but has not been verified in the current environment.
7. Optional BGE/FAISS retrieval is not part of the tested lightweight path.

These limitations are recorded explicitly instead of being hidden behind a
single aggregate score.

## Five-minute presentation structure

1. Show the same question in Naive RAG and TruthGuard.
2. Point out that Naive RAG gives one fluent value without exposing the old
   source or exception.
3. Show TruthGuard's conflicting positions and exact citations.
4. Show the supersession graph and trust breakdown.
5. Demonstrate the T6 question and calibrated abstention.
6. Demonstrate the T7 question and not-in-corpus behavior.
7. End with benchmark metrics and honest limitations.

## Repository status

The local product is demo-ready. The project is submission-ready when the
remaining evidence tasks in `docs/PROJECT_GUIDE.md` are either completed or
explicitly marked as unavailable due to provider, Docker, or human-review
constraints.
