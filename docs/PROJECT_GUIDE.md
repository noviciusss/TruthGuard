# TruthGuard Project Guide

TruthGuard is a local prototype for exposing disagreement in document question
answering. This guide complements the [README](../README.md),
[architecture](ARCHITECTURE.md), [demo script](DEMO_SCRIPT.md), and
[submission pitch](../SUBMISSION.md).

## 1. What the local system does

The fictional Aurelia Health corpus contains policies, amendments, circulars,
FAQs, manuals, and notices with deliberate disagreements. The pipeline:

1. Retrieves section-aware passages with hybrid search.
2. Expands toward amendments, exceptions, and supersession-graph neighbors.
3. Drafts an answer from retrieved passages.
4. Checks draft claims and identifies competing document positions.
5. Assigns conflict types and transparent trust factors.
6. Resolves, answers conditionally, abstains, or reports missing evidence.
7. Shows citations, conflicts, trust breakdowns, and a trace in Streamlit.

The deterministic implementation is a bounded policy-domain prototype, not a
general semantic verifier. A separate optional LLM critic performs structured
claim extraction, conflict detection, and self-critique. These paths must be
identified separately in presentations and results.

## 2. Important files

| Path | Purpose |
|---|---|
| `app/streamlit_app.py` | Streamlit user interface |
| `src/truthguard/api.py` | FastAPI query service |
| `src/truthguard/pipeline.py` | Manual state machine and optional LangGraph adapter |
| `src/truthguard/llm.py` | Provider routing, cache, budgets, and retries |
| `src/truthguard/schemas.py` | Structured data contracts |
| `src/truthguard/agents/critic.py` | Deterministic and LLM critic paths |
| `src/truthguard/agents/trust.py` | Inspectable trust arithmetic |
| `src/truthguard/agents/resolver.py` | Resolution and abstention decisions |
| `src/truthguard/ingest/index.py` | Hybrid retrieval and optional BGE/FAISS |
| `src/truthguard/graph/supersession.py` | Document and section amendment graph |
| `data/factsheet/aurelia_facts.yaml` | Shared synthetic ground truth |
| `data/benchmark/eval_subset_40.jsonl` | Frozen quota-limited evaluation selection |
| `bench/metrics.py` | Proxy metric definitions and bootstrap intervals |
| `requirements.lock` | Core runtime + pytest dependency closure |
| `requirements-ml.lock` | Optional CPU retrieval closure beyond core |
| `requirements-orchestration.lock` | Optional LangGraph closure beyond core |

## 3. Setup and local execution

Use Linux x86_64, Python **3.11.2** with `venv`, GNU Make, and Git. The runtime
is pinned in `.python-version`. From the repository root:

```bash
python3 --version  # expected: Python 3.11.2
make install
test -e .env || cp .env.example .env
make test
make smoke
make compile
```

`make install` creates `.venv`, pins pip to `26.2.1`, installs
`requirements.lock`, and runs `pip check`. It requires package-index access or
locally supplied wheels. `make test` is the single offline test entry point
after setup and does not require provider credentials or model downloads.

Optional stacks install their closure alongside the shared core pins:

```bash
make install-ml
make install-orchestration
```

The first adds CPU Torch and BGE/FAISS dependencies; it does not bundle or pin a
model-weight revision. The second adds LangGraph; the manual pipeline works
without it. Offline mode uses hash embeddings by default even if ML packages
are installed. Locks cover the Python 3.11.2/Linux x86_64 dependency closure,
not every operating system, optional extra, or package artifact hash.

Start either interface explicitly offline:

```bash
TRUTHGUARD_OFFLINE=true make ui
# http://127.0.0.1:8501
```

```bash
TRUTHGUARD_OFFLINE=true make api
# http://127.0.0.1:8000/docs
```

For a repeatable scripted demonstration, `make demo` writes
`reports/demo_output.md`. It demonstrates selected cases; it is not a held-out
accuracy test. See the [demo script](DEMO_SCRIPT.md) for speaking notes.

Live configuration is read from `.env` and `config.yaml`. Live synthesis and
LLM criticism depend on configured keys, actual successful role chains, and
quota availability. A configured provider name alone is not evidence that it
served a result. Keep credentials and generated provider state local.

## 4. Container packaging and deployment

The Dockerfile installs Make/Git and the core lock on Python 3.11.2. It copies
source, tests, scripts, synthetic inputs, and Markdown reports, and contains
`make test PYTHON=python` as a build step. Local `.env`, model caches, provider
SQLite state, and raw live-evaluation JSONL outputs are not copied into the
image. Optional ML/orchestration packages are not part of the core image.

Exact Docker build, offline test, UI deployment, and API deployment commands
are in the [README](../README.md). Docker is unavailable in the packaging
environment: build, build-time tests, and runtime startup are all unverified.
No public deployment has been validated. The base image uses a version tag,
not a digest, and Debian packages are not snapshot-pinned.

## 5. Evidence: what each result means

### Generated benchmark

There are 35 synthetic documents and 180 generated, templated questions
(40 development / 140 test), derived from the same factsheet. The frozen test
split is useful for implementation checks, but shares vocabulary, facts, and
construction patterns with the system's synthetic domain. It is not an
independently collected real-world benchmark.

The historical 140-question run used live Groq synthesis **and a deterministic
critic**, recording answer-proxy accuracy `0.8286` and conflict F1 `0.8374`.
The complete B0/B1/B2 comparison in [results](../reports/results.md) is offline.
These records are not fresh measurements of subsequent changes and do not
establish live-model or LLM-critic superiority.

### Wild robustness before/after

The historical 20-question offline result compares hash/BM25 with
BGE/FAISS/BM25: answer-proxy accuracy **0.35 → 0.45**, conflict F1
`0.4348 → 0.4800`. Both used offline reformulations and the deterministic
critic. Live reformulation and LLM-critic improvements have not been measured
by that table. Both T0 controls were falsely flagged in those historical runs.

The newer DEV-selected fact-level fix held BGE retrieval fixed and measured:

| Split | T0 false positives before → after | Answer proxy before → after |
|---|---|---|
| DEV (40) | 1/2 → 0/2 | 0.8500 → 0.8500 |
| TEST (140) | 15/18 → 0/18 | 0.8286 → 0.8214 |
| wild (20) | 2/2 → 0/2 | 0.4500 → 0.4000 |

Wild conflict recall also fell from 0.3750 to 0.3125. Explain this honestly as
a precision/recall trade-off, not general robustness success. TEST/wild were
evaluation only; no threshold selection used those outcomes. Per-question
evidence and commands are in [false-conflict results](../reports/false_conflicts.md).

### Programmatic audit and decision blocker

The [offline corpus audit](../reports/corpus_audit_programmatic.md) checked all
180 main questions, 20 wild questions, and the overlapping fixed40 subset.
Across 200 unique questions, 100 pass applicable mechanical checks and 100 are
unverifiable. No semantic pass is inferred from a lexical T7 no-hit or composed
answer quantity overlap. Seven documents retain corrupted versions; all seven
missing effective dates recover.

The annual-limit notice contradicts itself (500000 versus 600000), and later
material complicates the T6 whole-corpus abstention labels. Corpus/question
changes require adjudication. No gold files have been changed; work pauses
before ablations or additional live experiments.

### Quota-limited fixed40 experiment

The committed subset has six questions each for T1–T6 and two each for T0/T7.
Reuse that selection for future measurement. The offline BGE deterministic
run completed 40/40; it is an end-to-end baseline, not a controlled critic-only
ablation. The live run reached only seven successful answers, eighteen failures,
and fifteen unreached questions before timeout. Successful critic calls used
Groq Qwen; synthesis used Groq GPT-OSS. Failed Mistral attempts do not establish
fallback success, and this is not Gemini-critic validation.

**The partial live run is not comparative results.** Its successes are
availability-biased, and upstream contexts/drafts differed from the offline
baseline. Rate limits, request sizing, and fallback availability blocked the
intended comparison. See [fixed40 status](../reports/critic_subset_status.md).

### Metric interpretation

- `provenance_correctness` checks document-ID overlap on conflict questions;
  on other questions it checks citation presence. It is document-level
  provenance, **not semantic support**, correct-span validation, or proof that
  all competing sources were retrieved.
- Answer accuracy uses numeric/substring matching, with status-based scoring
  for T6/T7; describe it as a proxy rather than human semantic accuracy.
- The blended-answer metric is a conflict/status proxy, not an independent
  semantic judgment. Zero does not prove that no incompatible values were
  blended.
- Mocked structured-call tests validate mechanics, not live critic quality or
  cross-provider lineage separation.

## 6. Packaging validation and remaining dependencies

Core and combined core+ML+orchestration resolution passed
`pip install --dry-run --ignore-installed` on Linux x86_64 / Python 3.11.2.
Pins retain installed versions where available and add only missing packages
from the relevant resolver closure. This avoids freezing unrelated environment
packages. A dry-run is not a clean-install or runtime validation.

The existing virtualenv runs the offline tests but fails `pip check` for six
missing dependencies: `ipython`, `altair`, `gitpython`, `pandas`, `pydeck`, and
`rich`. All are included in the new core lock. No fresh install was executed
during this packaging pass. Still unverified:

1. Actual core installation and Streamlit/PyVis startup from the locks in a
   clean virtualenv; offline tests alone do not exercise the full UI tree.
2. Optional CPU ML and LangGraph runtime behavior with the complete locked
   environment, and provisioning of separately downloaded model weights.
3. Docker image build, offline container tests, and both interface startups.
4. Controlled fixed40 comparison with contexts/drafts held constant, and live
   baseline comparison within available quotas, only after offline gates.
5. Human gold-label review and adjudication of the completed mechanical audit.

## 7. Presentation guidance

Lead with visible disagreement and inspectable decisions. Show supersession,
scope, an exception, same-authority abstention, and a question absent from the
corpus. Explain that deterministic checks are useful but domain-specific, and
that optional LLM criticism still needs a completed controlled evaluation.
Close with the synthetic/templated data limitation and the historical wild
robustness gap rather than a single aggregate accuracy claim.
