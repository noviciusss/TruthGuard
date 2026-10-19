# TruthGuard Progress

## Project decisions from the user

- Use `.env.example`; the user will fill provider credentials locally.
- Groq is the primary runtime provider.
- Live free-tier APIs are approved when needed, with strict rate-limit and
  caching discipline.
- Initial deployment target is local or Docker. Docker verification will be
  requested from the user when it becomes necessary.
- The six-day deadline is not being enforced as a hard constraint.
- Pitch/deck/video work is optional and belongs in the final phase.

## Current status

- Phase: 2 — synthetic corpus
- Status: complete
- Last updated: 2026-10-19

## Phase 0 — Foundation

### Completed

- Initialized a Git repository.
- Added Python 3.11.2 pin.
- Added project-level environment example with Groq as the primary provider.
- Added pinned runtime and development dependency files.
- Added configuration for retrieval, authority, trust weights, providers,
  role chains, limits, and evaluation settings.
- Added Makefile commands for install, test, compile, and smoke checks.
- Added Dockerfile and initial README.
- Added this progress log.
- Added the planned package, data, benchmark, app, and report directories.

### Tests run

| Command | Result |
|---|---|
| `python3 --version` | Passed: Python 3.11.2 |
| `docker --version` | Not available in the current environment |
| `pytest --version` | Not available globally; project virtualenv still needs setup |
| `make test` | Passed: 4 tests |
| `make smoke` | Passed: configuration loaded in offline mode |
| `make compile` | Passed: Python source compilation; empty phase directories now exist |

### Problems and deviations

- No application code existed before this phase; the runtime skeleton is now
  in place.
- Docker cannot be verified in the current environment because the Docker
  executable is unavailable.
- The initial dependency lock is represented by exact pinned requirements;
  a fully resolved wheel lock will be validated during installation.

### Required input

- No input is required to continue foundation implementation.
- A Groq API key will be needed only before live provider calls.

### Next step

Implement metadata parsing, section-aware chunking, hybrid retrieval, and the
supersession graph over the generated corpus.

## Phase 1 — Schemas and provider router

### Completed

- Added Pydantic v2 schemas for document metadata, chunks, spans, claims,
  conflicts including T0 and T7, trust scores, agent trace, final answers,
  benchmark questions, and LLM accounting.
- Added strict structured-output validation with useful field bounds.
- Added an HTTP-based multi-provider router with Groq-first role chains,
  configured lineage-separated critic/judge fallbacks, and no provider SDK
  lock-in.
- Added SQLite response caching keyed by provider, model, messages, and
  parameters.
- Added persisted call logs, RPM/RPD counters, budget status, fallback
  handling, and one schema-repair retry.
- Added offline fixture mode so tests and deterministic development do not
  require API keys or network access.

### Files changed

- `src/truthguard/schemas.py`
- `src/truthguard/llm.py`
- `tests/test_schemas.py`
- `tests/test_llm.py`

### Tests run

| Command | Result |
|---|---|
| `make test` | Passed: 10 tests |
| `make smoke` | Passed: configuration loaded in offline mode |
| `make compile` | Passed |

### Problems and deviations

- Live providers have not been called. Their exact free-tier limits and model
  availability must be checked in the provider consoles before bulk work.
- The router uses OpenAI-compatible HTTP endpoints rather than provider SDKs;
  this is intentional to reduce dependency churn and simplify mocks.
- The full runtime dependency set is not installed yet; only the packages
  required for the current offline phase are installed in `.venv`.

### Required input

- No input is needed for the next phase.
- A Groq API key will be requested before the first live corpus-generation
  smoke test.

## Phase 2 — Synthetic factsheet and corpus generator

### Completed

- Added the hand-written Aurelia Health ground-truth factsheet with 14
  versioned facts, dates, scopes, and source notes.
- Added a deterministic 35-document generator covering policies, amendments,
  circulars, FAQs, manuals, and notices.
- Added deliberate T0–T7 manifest entries, including temporal,
  scope, numeric, definitional, implicit, unresolvable, control, and
  unanswerable cases.
- Added deterministic metadata corruption to 14/35 documents (40%), while
  retaining the expected metadata in the manifest for later inference tests.
- Generated and committed the corpus documents and `corpus_manifest.json`.
- Added fact-use validation so each fact is represented between two and five
  times.
- Added reproducibility and content tests.

### Review sample

The generated sample requested by the specification is available at:

- `data/corpus/POL-2024-V1.md` — stale 30-day wording with missing header
  effective date.
- `data/corpus/AMD-2025-03.md` — 45-day amendment to Section 4.1.
- `data/corpus/CIR-2025-08-A.md` and `CIR-2025-08-B.md` — same-date,
  same-authority 500000 versus 600000 annual limits for T6 abstention.
- `data/corpus/corpus_manifest.json` — gold conflict manifest and metadata
  corruption statistics.

### Files changed

- `data/factsheet/aurelia_facts.yaml`
- `bench/generate_corpus.py`
- `data/corpus/*.md`
- `data/corpus/corpus_manifest.json`
- `tests/test_corpus.py`

### Tests run

| Command | Result |
|---|---|
| `make test` | Passed: 13 tests |
| `PYTHONPATH=src .venv/bin/python -m bench.generate_corpus` | Passed: 35 documents, 40% metadata corruption |
| `make compile` | Passed |
| `git diff --check` | Passed |

### Problems and deviations

- The corpus is currently template-generated and deterministic. The required
  second-LLM audit is explicitly recorded as pending and will be added after
  the benchmark/evaluation path can consume it without spending calls during
  local tests.
- YAML date scalars are normalized during loading because PyYAML parses ISO
  dates as `date` objects.
- The generated corpus is synthetic and contains no private or real health
  information.

### Required input

- No input is needed to implement ingestion and graph logic.
- Before the first live corpus audit, I will ask for a filled `GROQ_API_KEY`
  in your local `.env` and confirm the provider's current free-tier limits.

## Open issues

- Confirm exact free-tier limits in the provider consoles before bulk runs.
- Decide whether to verify Docker locally when the application image is ready.
- Hand verification of 30 benchmark questions will be requested after the
  benchmark is generated.
