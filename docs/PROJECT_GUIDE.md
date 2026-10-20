# TruthGuard Project Guide

This document explains what has been built, how the scripts fit together, how
to run the project, how to explain the approach to a judge, what is complete,
and what evidence still remains. It is the detailed companion to the shorter
[`README.md`](../README.md) and [`SUBMISSION.md`](../SUBMISSION.md).

## Status at a glance

- **Core product:** complete.
- **Offline tests and demo:** complete.
- **Live TruthGuard test split:** complete, 140/140 questions.
- **Judge-ready local UI:** complete.
- **Live Gemini critic:** implemented, but not yet stable enough for benchmark
  metrics because of free-tier availability and fallback quota issues.
- **Human review, corpus audit, live baselines, and Docker verification:**
  pending evidence tasks.

## 1. What TruthGuard does

TruthGuard answers questions over a deliberately inconsistent synthetic
insurance corpus. It does **not** simply blend the first passages it retrieves.
Instead it:

1. Retrieves relevant passages using hybrid search.
2. Drafts an answer from those passages.
3. Decomposes the draft into claims.
4. Checks claims against all retrieved evidence.
5. Detects and types conflicts as T0–T7.
6. Scores each source transparently.
7. Resolves, answers conditionally, or abstains.
8. Shows citations and the agent trace in the UI.

The domain is fictional **Aurelia Health**. No real health or customer data is
used.

## 2. What is complete

### Core foundation

- Python 3.11.2 project setup.
- Git history with phase commits.
- `.env.example` for credentials.
- Offline test mode.
- SQLite response cache and provider call accounting.
- Groq-first provider routing with fallback configuration.
- Structured Pydantic schemas.

### Corpus and benchmark

- 35 synthetic policy, amendment, circular, FAQ, manual, and notice documents.
- 14 versioned facts in `data/factsheet/aurelia_facts.yaml`.
- 40% intentionally corrupted or incomplete document metadata.
- Conflict manifest covering T0–T7.
- 180 benchmark questions:
  - 40 development questions
  - 140 test questions
  - 36 marked multi-hop

### Reasoning system

- BM25 retrieval.
- Deterministic dense fallback retrieval.
- Optional CPU BGE/FAISS stack.
- Reciprocal rank fusion.
- Conflict-seeking query expansion.
- Supersession graph with partial section amendments.
- Claim verification and conflict typing.
- Lineage-separated LLM critic path: Gemini Flash first, Mistral fallback,
  with three bounded structured calls and deterministic annotations. The path
  is implemented and tested with mocks; the complete reported benchmark uses
  the deterministic critic because live Gemini availability was intermittent.
- Trust scoring.
- Resolution and calibrated abstention.
- B0/B1/B2 baselines.
- Resumable evaluation.

Use `--no-llm-critic` with `bench.run_eval` to explicitly run the old
deterministic critic for the ablation comparison.

### User interfaces

- FastAPI API.
- Streamlit UI with:
  - Ask screen
  - T1–T6 example questions
  - Status cards
  - Highlighted citations
  - Claim verdicts
  - Conflict positions
  - Trust breakdowns
  - Supersession graph
  - Agent trace
  - Naive RAG comparison
  - Benchmark results

## 3. Important files

| Path | Purpose |
|---|---|
| `app/streamlit_app.py` | Streamlit user interface |
| `src/truthguard/pipeline.py` | End-to-end TruthGuard flow |
| `src/truthguard/llm.py` | Provider routing, caching, budgets, retries |
| `src/truthguard/schemas.py` | Structured data contracts |
| `src/truthguard/agents/critic.py` | Claim and conflict checking |
| `src/truthguard/agents/trust.py` | Transparent trust arithmetic |
| `src/truthguard/agents/resolver.py` | Resolve/contextual/abstain decisions |
| `src/truthguard/ingest/metadata.py` | Metadata inference |
| `src/truthguard/ingest/index.py` | Hybrid retrieval index |
| `src/truthguard/graph/supersession.py` | Supersession graph |
| `bench/generate_corpus.py` | Generate the synthetic corpus |
| `bench/generate_questions.py` | Generate the 180-question benchmark |
| `bench/run_eval.py` | Resumable evaluation runner |
| `bench/metrics.py` | Evaluation metrics and bootstrap intervals |
| `bench/ablations.py` | Ablation runner |
| `reports/progress.md` | Phase history and checks |
| `reports/results.md` | Live and offline evaluation results |

## 4. How to run it

### First-time setup

```bash
cp .env.example .env
# Put GROQ_API_KEY in .env if live calls are needed.
make install
```

For local tests, keep this in `.env`:

```env
TRUTHGUARD_OFFLINE=true
```

The loader handles `.env` files created on Windows with CRLF line endings.

### Run the checks

```bash
make test
make compile
make smoke
```

The primary test command is `make test`. It does not need an API key or
network access.

### Start the UI

```bash
make ui
```

Open:

```text
http://127.0.0.1:8501
```

### Start the API

```bash
make api
```

Open the API documentation at:

```text
http://127.0.0.1:8000/docs
```

Example API request:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the hospitalization waiting period?"}'
```

### Regenerate data

```bash
PYTHONPATH=src .venv/bin/python -m bench.generate_corpus
PYTHONPATH=src .venv/bin/python -m bench.generate_questions
```

### Run offline evaluation

```bash
PYTHONPATH=src .venv/bin/python -m bench.run_eval \
  --questions data/benchmark/questions.jsonl \
  --output /tmp/truthguard-offline.jsonl \
  --system truthguard \
  --split test
```

Available systems are `b0`, `b1`, `b2`, and `truthguard`.

### Run live Groq evaluation

Set:

```env
TRUTHGUARD_OFFLINE=false
GROQ_API_KEY=your-key
```

Then use a small bounded run first:

```bash
PYTHONPATH=src .venv/bin/python -m bench.run_eval \
  --questions data/benchmark/questions.jsonl \
  --output reports/live_eval_dev.jsonl \
  --system truthguard \
  --split dev \
  --limit 5
```

The evaluator writes one record at a time and retries failed records on the
next run. This is important because free-tier daily and token-per-minute
limits can stop a run.

## 5. What remains

### Required before calling the project fully competition-ready

1. Hand-review 30 benchmark questions and record agreement.
2. Run the second-LLM corpus audit against the conflict manifest.
3. Exercise the Gemini/Mistral lineage-separated critic if that architecture
   claim is required in the presentation.
4. Run live B0/B1/B2 baselines using a fallback provider or after a quota
   reset.
5. Verify the Docker build on a machine with Docker.

The product is already **demo-ready**. These are evidence and packaging gates,
not blockers for explaining or showing the local application.

### Optional improvements

- Install `requirements-ml.txt` and test BGE/FAISS retrieval.
- Install `requirements-orchestration.txt` and run `compile_langgraph()`.
- Add charts as image assets to the benchmark tab.
- Add screenshots or a recorded demo after the local walkthrough is approved.

The manually written wild set can now be evaluated reproducibly with:

```bash
make wild
```

This writes `reports/wild_results.md` and keeps the robustness result separate
from the official frozen test score.

The current offline wild result is intentionally not presented as a success
metric: answer accuracy is `0.3500`, conflict F1 is `0.4348`, and abstention
recall is `0.7500`. The gap indicates that indirect and mixed-topic questions
need better query planning or a stronger live critic before they are used as a
headline claim.

## 6. Current evidence

The latest results are in `reports/results.md`.

The live TruthGuard test split completed 140/140 questions using the
deterministic critic path with Groq synthesis:

- Answer accuracy: 0.8286
- Conflict F1: 0.8374
- Conflict type accuracy: 0.6071
- Resolution-mode accuracy: 0.7643
- Provenance correctness: 1.0
- Blended-answer rate: 0.0
- Abstention recall: 1.0

These results are on a synthetic benchmark and should be presented as
architecture evidence, not production accuracy. Do not describe them as
Gemini-critic results.

## 7. What is needed from the owner

1. **Human review:** verify 30 gold questions.
2. **Provider keys:** Gemini for critic lineage; Mistral/OpenRouter for live
   baselines and fallback resilience.
3. **Docker check:** run `docker build` and `docker run` on your machine.
4. **Presentation decision:** decide whether to add the optional pitch/video
   materials.
5. **Deployment decision:** if local use is enough, stop at the local UI; if a
   public demo is required, choose a deployment target and provide access.

## 8. How to explain the approach

### The problem in plain language

Ordinary RAG finds relevant text, but it usually assumes the text agrees. In a
versioned policy corpus that can create a confident answer from incompatible
documents.

### TruthGuard's answer

TruthGuard makes disagreement a first-class object. It does not stop after
retrieving one passage. It searches for related amendments and exceptions,
checks the draft claim by claim, compares document positions, and uses the
supersession graph and trust factors before resolving.

### The four user-visible outcomes

1. **Resolved:** one current supported source wins.
2. **Conditional:** different values apply to different scopes or conditions.
3. **Abstained:** sources conflict and no defensible winner exists.
4. **Not in corpus:** the evidence base does not answer the question.

### The strongest demo sentence

> TruthGuard does not just answer from retrieved text; it tells me when the
> retrieved text disagrees, why one source wins, and when it is safer not to
> choose.

### Recommended judge flow

Run `make demo` or open the Streamlit UI and show, in order:

1. T1 waiting-period supersession.
2. T2 age-based co-payment scope.
3. T5 planned-versus-emergency exception.
4. T6 same-authority abstention.
5. T7 not-in-corpus behavior.

The full speaking notes are in [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md), and the
component explanation is in [`ARCHITECTURE.md`](ARCHITECTURE.md).

## 9. Submission checklist

- [x] Offline test suite passes.
- [x] Reproducible offline judge demo exists.
- [x] Streamlit and FastAPI interfaces exist.
- [x] 140-question live TruthGuard test split is recorded.
- [x] Results distinguish deterministic, offline, and live paths.
- [x] Submission summary and architecture explanation exist.
- [ ] Human review fields are completed.
- [ ] Independent corpus audit is completed.
- [ ] Live B0/B1/B2 comparison is completed.
- [ ] Gemini critic smoke is stable enough for a reported live critic result.
- [ ] Docker is verified on a Docker-capable machine.
