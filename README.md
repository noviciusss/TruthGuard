# TruthGuard

TruthGuard is an offline-first hackathon submission for adversarial verification of
multi-agent document question answering over a deliberately inconsistent,
synthetic Aurelia Health corpus.

The system is designed to expose disagreement rather than silently blending
contradictory sources. Its core flow is retrieval, drafting, claim-level
verification, conflict typing, transparent trust scoring, and either
resolution or calibrated abstention.

## Current status

The core product and offline demo are complete. The project is demo-ready and
has a complete 140-question live TruthGuard evaluation. Remaining submission
evidence is explicitly separated: human review, independent corpus audit,
live baseline comparison, live Gemini-critic validation, and Docker
verification. See [`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md) for the
full explanation and [`SUBMISSION.md`](SUBMISSION.md) for the judge-facing
summary.

For a plain-language explanation of the architecture, scripts, run commands,
remaining work, and required owner inputs, see
[`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md).

## Requirements

- Python 3.11.2
- Git
- Docker is optional and will be verified when requested
- API keys are optional for offline tests and required only for live generation

## Setup

```bash
cp .env.example .env
# Fill provider keys only when live calls are needed.
make install
```

Keep `TRUTHGUARD_OFFLINE=true` for local tests. Set
`TRUTHGUARD_OFFLINE=false` only for live Groq generation/evaluation. The
loader reads the project-local `.env` automatically, including files created
on Windows with CRLF line endings.

The core install intentionally stays light and uses a deterministic dense
embedding fallback. To install the optional CPU-only BGE/FAISS retrieval stack
(which downloads a large Torch wheel), run:

```bash
make install-ml
```

The application uses a tested manual state-machine fallback by default. To
install and exercise the optional LangGraph adapter, run:

```bash
make install-orchestration
```

Groq is the primary provider for synthesis and bulk generation. Gemini is the
lineage-separated critic, with Mistral configured as a fallback. The provider
router caches responses, persists call counts, and enforces request/token
budgets. The complete offline path does not require any provider key.

## Checks

The single offline test command is:

```bash
make test
```

Additional checks:

```bash
make smoke
make compile
make demo
make wild
```

Tests and the judge demo do not require an API key, network access, or
downloaded model files. Live evaluation is separate and quota-aware.

## Local run

Start the API:

```bash
make api
# http://127.0.0.1:8000/docs
```

Start the Streamlit demo in another terminal:

```bash
make ui
# http://127.0.0.1:8501
```

The UI includes Ask, compare mode, claim verification, conflict positions,
trust breakdowns, citations, and agent trace. It runs in offline mode unless
you explicitly change `TRUTHGUARD_OFFLINE` and provide provider credentials.

For a repeatable six-question judge walkthrough without starting the UI:

```bash
make demo
# writes reports/demo_output.md
```

The optional Docker run uses the same local configuration:

```bash
docker build -t truthguard .
docker run --rm --env-file .env -p 8501:8501 truthguard
```

## Safety and data

The corpus is fully synthetic. Do not put private health, customer, or
production documents into the project or send them to free-tier providers.
Never commit `.env`, API keys, model caches, or generated runtime databases.

## Explain TruthGuard in one minute

Ordinary RAG retrieves passages and asks a model to blend them into one answer.
That fails when the corpus contains old policies, amendments, exceptions, or
same-authority disagreements. TruthGuard treats disagreement as a first-class
object. It retrieves evidence, drafts a candidate answer, decomposes it into
atomic claims, checks every claim against the retrieved passages, compares
document positions, follows supersession links, scores source trust, and then
chooses a resolved, conditional, abstained, or not-in-corpus response.

The differentiator is **auditable conflict handling**: the UI shows what
disagreed, why one source won, or why the system refused to choose.

## Evidence status

The committed benchmark contains 180 synthetic questions: 40 development and
140 test questions. The final live TruthGuard test run completed 140/140
questions with answer accuracy `0.8286`, conflict F1 `0.8374`, provenance
correctness `1.0`, blended-answer rate `0.0`, and abstention recall `1.0`.
These figures were produced by the deterministic critic path, not the live
Gemini critic. Offline baseline comparisons and limitations are documented in
[`reports/results.md`](reports/results.md).
