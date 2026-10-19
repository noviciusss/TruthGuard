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

- Phase: 0 — foundation
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

Implement Pydantic schemas and the offline-first provider router, then run the
second phase test gate.

## Open issues

- Confirm exact free-tier limits in the provider consoles before bulk runs.
- Decide whether to verify Docker locally when the application image is ready.
- Hand verification of 30 benchmark questions will be requested after the
  benchmark is generated.
