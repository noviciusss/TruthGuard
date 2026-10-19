# TruthGuard

TruthGuard is an offline-first prototype for adversarial verification of
multi-agent document question answering over a deliberately inconsistent,
synthetic Aurelia Health corpus.

The system is designed to expose disagreement rather than silently blending
contradictory sources. Its core flow is retrieval, drafting, claim-level
verification, conflict typing, transparent trust scoring, and either
resolution or calibrated abstention.

## Current status

The repository is being built phase by phase. The current progress, checks,
deviations, and required inputs are tracked in
[`reports/progress.md`](reports/progress.md).

## Requirements

- Python 3.11.2
- Git
- Docker is optional and will be verified when requested
- API keys are optional for offline tests and required only for live generation

## Setup

```bash
cp .env.example .env
# Fill GROQ_API_KEY when live Groq calls are needed.
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

Groq is the primary provider for synthesis and bulk generation. Gemini,
Mistral, and OpenRouter are configured as lineage-separated roles or fallbacks
to respect the specification and reduce the chance that one free-tier limit
blocks a run. The provider router caches responses and persists call counts.

## Checks

The single offline test command is:

```bash
make test
```

Additional checks:

```bash
make smoke
make compile
```

Tests must not require an API key, network access, or downloaded model files.
Live corpus generation and evaluation are separate commands and will be added
as their phases are implemented.

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

The optional Docker run uses the same local configuration:

```bash
docker build -t truthguard .
docker run --rm --env-file .env -p 8501:8501 truthguard
```

## Safety and data

The corpus is fully synthetic. Do not put private health, customer, or
production documents into the project or send them to free-tier providers.
Never commit `.env`, API keys, model caches, or generated runtime databases.
