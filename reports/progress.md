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

- Phase: 1 — schemas and provider router
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

Build the synthetic Aurelia Health fact sheet and deterministic corpus
generator, then run the corpus validation gate.

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

## Open issues

- Confirm exact free-tier limits in the provider consoles before bulk runs.
- Decide whether to verify Docker locally when the application image is ready.
- Hand verification of 30 benchmark questions will be requested after the
  benchmark is generated.
