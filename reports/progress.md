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

- Phase: 9 — project guide and UI usability pass
- Status: complete; local UI and API verified
- Last updated: 2026-10-20

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

### Historical next step

Implement the retriever agent, synthesizer, and baseline answer flows over the
indexed corpus.

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

## Phase 3 — Ingestion, retrieval, and supersession graph

### Completed

- Added metadata parsing for front matter, body effective dates, supersession
  references, amendment references, fuzzy document IDs, filename fallbacks,
  authority rank, and metadata confidence.
- Preserved unknown dates as unknown; filename hints are used only as the
  documented fallback.
- Added Markdown loader and section-aware chunking with exact character
  offsets and document metadata attached to every chunk.
- Added hybrid retrieval with BM25, deterministic dense fallback embeddings,
  reciprocal rank fusion, result score breakdowns, and JSON save/load.
- Added a networkx supersession graph with document-level and partial
  section-level edges, latest-valid selection, chains, neighbors, cycle
  detection, as-of handling, and missing-date behavior.
- Regenerated the corpus so amendment metadata is present in both headers and
  body text for inference tests.

### Files changed

- `src/truthguard/ingest/metadata.py`
- `src/truthguard/ingest/loader.py`
- `src/truthguard/ingest/chunker.py`
- `src/truthguard/ingest/index.py`
- `src/truthguard/graph/supersession.py`
- `bench/generate_corpus.py`
- `data/corpus/*.md`
- `data/corpus/corpus_manifest.json`
- `tests/test_ingest_graph.py`

### Tests run

| Command | Result |
|---|---|
| `make test` | Passed: 18 tests |
| `PYTHONPATH=src .venv/bin/python -m bench.generate_corpus` | Passed: 35 documents, 40% metadata corruption |
| Retrieval smoke query | Passed: 35 docs, 182 chunks; both stale and amendment waiting-period sources appeared in top 8 results |
| `make compile` | Passed |

### Problems and deviations

- Dense retrieval currently defaults to a deterministic hash embedder so tests
  do not download `bge-small-en-v1.5`. The optional sentence-transformers
  backend remains in the pinned runtime requirements and will be wired for
  live evaluation after the core pipeline is stable.
- The generated corpus now includes body effective-date statements, so a
  missing header date can be recovered. This is intentional metadata-inference
  test data, not accidental clean metadata.
- Metadata inference and graph logic are implemented, but the full benchmark
  question set and LLM audit are still pending.

### Required input

- No input is needed for the retriever implementation.
- I will request Groq credentials before a live reformulation or corpus-audit
  call; offline tests will continue to use fixtures.

## Phase 4 — Benchmark, retriever agent, synthesizer, and baselines

### Completed

- Added deterministic benchmark generation with exactly 180 labeled questions:
  24 each for T1–T6, 20 T0 controls, and 16 T7 unanswerable cases.
- Added fixed 40-question dev and 140-question test splits, 36 multi-hop
  markers, paraphrase groups, and a not-yet-verified hand-review flag.
- Added conflict-seeking reformulation support with a deterministic offline
  path and a live structured provider path limited to two reformulations.
- Added graph-neighbor expansion to the retriever while retaining the original
  query's ranking priority.
- Added passage-only synthesizer drafts with inline chunk citations.
- Added B0 naive RAG, B1 recency RAG, and B2 self-consistency baselines.
- Generated and committed `data/benchmark/questions.jsonl`.

### Tests run

| Command | Result |
|---|---|
| `make test` | Passed: 23 tests at phase gate |
| `PYTHONPATH=src .venv/bin/python -m bench.generate_questions` | Passed: 180 questions |
| `make compile` | Passed |

### Problems and deviations

- The benchmark is template-generated and has not yet received the planned
  second-LLM audit or human review. All 30 hand-verification flags remain
  false until reviewed.
- The default local dense retriever is still the deterministic hash fallback;
  the BGE model is reserved for the live evaluation environment.

### Required input

- No input is needed for local agent work.
- The 30-question verification file will be prepared when the benchmark UI
  or review report is added.

## Phase 5 — Critic, resolver, pipeline, and evaluation foundations

### Completed

- Added claim decomposition, lexical grounding, unsupported-claim detection,
  topic-clustered contradiction checks, staleness-aware conflict typing, and a
  recorded self-critique pass.
- Added deterministic T1–T6 conflict detection with T0 false-positive control
  and T7 not-in-corpus handling.
- Added transparent trust scoring for recency, authority, specificity,
  corroboration, and metadata confidence.
- Added resolver modes for supersession, contextual answers, abstention,
  no-conflict answers, and not-in-corpus answers.
- Added trace-producing TruthGuard pipeline with a two-loop revision cap.
- Added an optional `compile_langgraph()` implementation; the manual path is
  the offline fallback when LangGraph is not installed.
- Added metric calculators for answer accuracy, conflict P/R/F1, type and
  resolution accuracy, provenance, unsupported claims, blended answers,
  abstention, false conflicts, and bootstrap CIs.
- Added resumable evaluation and ablation runners with persistent JSONL output.
- Verified the full taxonomy fixtures through the offline pipeline.

### Tests run

| Command | Result |
|---|---|
| `make test` | Passed: 34 tests |
| `make compile` | Passed |
| Offline pipeline taxonomy smoke | Passed: T1 resolved, T2 conditional, T3 resolved, T4 resolved, T5 conditional, T6 abstained, T0 no conflict, T7 not in corpus |
| `git diff --check` | Passed |

### Problems and deviations

- No live LLM call has been made. Provider prompts, Groq quota behavior, and
  the second-provider lineage separation still need a live smoke check.
- LangGraph is pinned but not installed in the current lightweight test
  virtualenv; the manual pipeline is what has actually been tested.
- Evaluation reports currently contain framework outputs, not final live
  benchmark numbers. Do not claim benchmark performance until live or audited
  cached results are run.

### Required input

- Before live generation/evaluation, provide `GROQ_API_KEY` in the local `.env`.
- If critic lineage separation is to be exercised live, also provide the
  Google AI Studio and Mistral keys; otherwise their configured fallbacks will
  remain unavailable and the run will stop clearly when all budgets are gone.

## Phase 6 — API, Streamlit UI, and documentation

### Completed

- Added FastAPI `/health` and `/query` endpoints with request validation and
  typed `FinalAnswer` responses.
- Added Streamlit Ask screen with taxonomy examples, optional as-of date,
  status badge, highlighted inline provenance, claim verdicts, conflict
  positions, trust-score breakdowns, citations, and agent trace.
- Added compare mode for B0 Naive RAG versus TruthGuard.
- Added supersession graph rendering with involved-document highlighting and
  effective-date labels when `pyvis` is available.
- Added benchmark tab and local run commands to the README and Makefile.
- Added `requirements.lock` and kept provider credentials in `.env.example`
  only.

### Tests run

| Command | Result |
|---|---|
| `make test` | Passed: 36 tests; one existing Starlette deprecation warning |
| `make compile` | Passed |
| `make smoke` | Passed |
| FastAPI TestClient health/query smoke | Passed |
| Streamlit server health smoke on `http://127.0.0.1:8502/_stcore/health` | Passed: `200 ok` |
| `git diff --check` | Passed |

### Problems and deviations

- Docker is still unverified because Docker is unavailable in this execution
  environment. The user should run the documented build when requested.
- Live provider evaluation and the second-LLM corpus audit remain pending;
  current tests intentionally stay offline.
- The benchmark tab displays generated result JSON when available; final
  polished result tables/charts and the optional pitch/video materials are
  deferred to the final optional phase.

### Required input

- Before live evaluation: fill `GROQ_API_KEY` in `.env` and tell me when it is
  ready. I will first run a tiny cached smoke request and check current free
  limits before any bulk job.
- If you want Docker verification now, run the Docker commands from the README
  and share the output if anything fails.

## Final local verification

### Checks run

| Command | Result |
|---|---|
| `PYTHONPATH=src .venv/bin/python -m bench.run_eval --questions data/benchmark/questions.jsonl --output /tmp/omnirush/truthguard-offline-smoke.jsonl --system truthguard --split dev --limit 5` | Passed: 5 records |
| Same resumable command a second time | Passed: 0 duplicate records |
| Offline dev evaluation, 40 questions | Passed: 40 records |

The 40-question offline development smoke produced provisional framework
metrics: answer accuracy 0.85, conflict F1 0.8923, type accuracy 0.725,
resolution-mode accuracy 0.825, provenance correctness 1.0, blended-answer
rate 0.0, and abstention recall 1.0. These are deterministic local smoke
numbers, not the required final test-set results and must not be presented as
the competition result.

## Phase 8 — Live execution after credentials were supplied

### Completed

- Confirmed `.env` exists without printing its values; `GROQ_API_KEY` is set.
- Added automatic local `.env` loading with CRLF normalization. This fixed the
  Windows-created `.env` path issue (`config.yaml\r`).
- Ran a live Groq structured-output smoke request successfully with provider
  `groq` and model `openai/gpt-oss-120b`.
- Ran a live end-to-end T1 pipeline successfully. It returned `resolved`, a
  T1 supersession conflict, citations, trust breakdown, and a four-step trace.
- Verified the FastAPI server in-process over HTTP: `/health` returned 200 and
  `/query` returned a resolved T1 answer.
- Verified Streamlit startup health at `http://127.0.0.1:8502/_stcore/health`
  with `200 ok` after the app finished indexing its corpus.
- Added provider 429 retry/backoff and RPM-window waiting.
- Added daily provider-budget hard stop so TPD exhaustion does not cause long
  repeated waits.
- Fixed resumable evaluation so failed/rate-limited records are retried rather
  than treated as completed.
- Completed all 40 live dev questions after retrying rate-limited records.
- Collected 88 successful live test answers before the Groq daily token budget
  was exhausted. The test run remains resumable in the ignored local file
  `reports/live_eval_test.jsonl`.

### Follow-up after new Groq account

- The user supplied a new unused Groq account.
- A schema-valid smoke call succeeded with Groq `openai/gpt-oss-120b`.
- The remaining 52 test questions resumed from the existing output and all
  completed successfully.
- Final live TruthGuard test coverage is now 140/140 questions.
- Consolidated results are recorded in `reports/results.md`.

### Live checks run

| Check | Result |
|---|---|
| `.env` presence/key-name check | Passed: key present; secret value not displayed |
| Correct-schema Groq smoke | Passed: Groq `openai/gpt-oss-120b` |
| Live T1 pipeline | Passed: resolved T1 with trace/citations |
| Live dev evaluation | Passed: 40/40 successful answers |
| Live test evaluation before account change | Partial: 88 successful answers; daily TPD exhaustion |
| Live test evaluation after new account | Passed: remaining 52 resumed; 140/140 latest successful answers |
| Offline full TruthGuard test split | Passed: 140/140 |
| Offline B0/B1/B2 full test split | Passed: 140/140 each |
| Final offline test suite | Passed: 37 tests |
| FastAPI in-process HTTP smoke | Passed: health 200; query 200 resolved T1 |
| Streamlit final health smoke | Passed: `200 ok` |
| `docker --version` | Not available in this environment |

### Live dev metrics

Computed from all 40 live dev answers with 95% bootstrap intervals:

- Answer accuracy: `0.85` (`0.725–0.95`)
- Conflict detection F1: `0.8923`
- Conflict type accuracy: `0.725` (`0.575–0.85`)
- Resolution-mode accuracy: `0.825` (`0.70–0.925`)
- Provenance correctness: `1.0`
- Unsupported-claim rate: `0.3271`
- Blended-answer rate: `0.0`
- Abstention recall: `1.0`
- False-conflict rate: `0.025`

These are live development metrics, not final test-set claims.

### Final live TruthGuard test metrics

The 140-question live test metrics are maintained in `reports/results.md`.
Highlights: answer accuracy `0.8286`, conflict F1 `0.8374`, conflict type
accuracy `0.6071`, resolution-mode accuracy `0.7643`, provenance correctness
`1.0`, blended-answer rate `0.0`, and abstention recall `1.0`.

### Offline full test comparison

The complete 140-question offline run completed for every system. These values
exercise the deterministic fallback and are not live model results:

| System | Answer accuracy | Conflict F1 | Type accuracy | Mode accuracy |
|---|---:|---:|---:|---:|
| B0 Naive RAG | 0.7429 | 0.0000 | 0.0000 | 0.1286 |
| B1 Recency RAG | 0.7429 | 0.0000 | 0.0000 | 0.1286 |
| B2 Self-consistency | 0.7429 | 0.0000 | 0.0000 | 0.1286 |
| TruthGuard | 0.8286 | 0.8374 | 0.6071 | 0.7643 |

### Problems and deviations

- Groq reported: `tokens per day (TPD): Limit 200000` during the first account
  run. A new user-supplied account was used to complete the remaining 52 test
  questions.
- Groq also exposed an 8,000-token/minute model limit. The router now waits
  and retries bounded 429 responses.
- Only Groq is configured. Gemini, Mistral, and OpenRouter fallbacks are
  unavailable, so they could not absorb the daily limit.
- Live B0/B1/B2 baseline runs were not started after the account change because
  the remaining daily token budget should not be spent without a fallback
  provider; the complete offline comparison is in `reports/results.md`.
- The live critic remains deterministic in the current implementation; the
  second-model critic lineage is not yet exercised live.
- Core tests, API, and UI work offline. The optional ML retrieval stack
  (`sentence-transformers`, BGE, FAISS, CPU Torch) is separated in
  `requirements-ml.txt` and was not installed because its large dependency
  transaction exceeded the sandbox install timeout.
- `make install` was retried after separating ML and orchestration dependencies;
  the environment's `/mnt/d` filesystem still timed out while installing the
  remaining Streamlit/Pandas transaction. The already-installed environment
  passes all checks; clean-machine installation should be verified on the
  user's Linux/Docker host.
- Docker remains unverified because Docker is not installed in this
  environment.

### Required input / next action

- Provide a Mistral/OpenRouter key if you want live B0/B1/B2 comparisons
  without consuming another Groq daily budget.
- If final architecture compliance is required, provide a Gemini key so the
  live critic lineage can be exercised after the test quota issue is resolved.
- Docker verification still requires you to run the Docker commands locally.

## Phase 9 — project guide and UI usability pass

### Completed

- Added `docs/PROJECT_GUIDE.md`, a plain-language explanation of the completed
  system, important files, scripts, commands, evidence, remaining work, and
  required owner inputs.
- Added a README link to the project guide.
- Improved the Streamlit UI with a styled hero header, sidebar control panel,
  status/claim/conflict/citation cards, clearer answer heading, and benchmark
  tab loading from the actual `reports/results.md` file.
- Kept the existing compare mode, claim evidence, trust breakdown, graph,
  citations, and trace behavior.

### Required input / next action

- Open the running UI at `http://127.0.0.1:8501` and test the six example
  questions.
- If you want public deployment, choose the target platform after reviewing
  the local UI.

### UI and API verification

| Check | Result |
|---|---|
| `http://127.0.0.1:8501/` | Passed: HTTP 200, Streamlit page served |
| `http://127.0.0.1:8501/_stcore/health` | Passed: `200 ok` |
| `http://127.0.0.1:8000/docs` | Passed: HTTP 200 |
| Offline T6 API query | Passed: `abstained`, conflict `T6` |

### Final review summary

The local product is ready for demonstration. The remaining work is not a
basic implementation blocker; it is evidence/completeness work:

1. Hand-review 30 benchmark questions.
2. Run the second-LLM corpus audit.
3. Add Gemini/Mistral/OpenRouter keys if live lineage-separated critic or live
   baseline evidence is needed.
4. Run Docker verification on the user's machine.
5. Decide whether the optional pitch/video phase is needed.

## Task 1 — Real lineage-separated LLM critic

### Completed implementation

- Added structured schemas for Critic Call A, B, and C.
- Added Gemini-first critic routing with Mistral fallback configuration;
  synthesizer remains Groq-configured.
- Added Call A for atomic claims and all-passage verdicts.
- Added Call B for clustered pairwise contradiction, staleness, and T1–T6
  typing using deterministic graph/metadata annotations.
- Added Call C self-critique that can drop false-positive conflicts; it is
  skipped when Call B finds no conflicts.
- Kept span matching, graph lookups, winner selection, and trust-score math in
  deterministic code.
- Added `--no-llm-critic` to `bench.run_eval` for the deterministic ablation.
- LLM critic mode disables revision loops so it never exceeds three critic
  calls per question.

### Tests and limitations

| Check | Result |
|---|---|
| `make test` | Passed: 39 tests |
| `make compile` | Passed |
| LLM critic mocked three-call flow | Passed: mode=llm, three calls, T1 output, trust breakdown |
| `--no-llm-critic` mocked guard | Passed: no LLM call, deterministic mode |
| Five-question live smoke | Blocked: 4/5 questions completed; Gemini 503/timeouts and Mistral 429 caused fallback failures |

The implementation is complete and the local keys are now present, but the
requested live lineage claim is not yet evidenced. The configured Gemini model
was corrected from the retired `gemini-2.0-flash` to `gemini-3.8-flash`.
The updated smoke reached Gemini successfully on some calls, but the provider
also returned HTTP 503 high-demand responses and read timeouts. Mistral
fallback calls returned HTTP 429 rate-limit responses. One of five questions
therefore failed after Groq's JSON endpoint rejected the request and OpenRouter
was unavailable. Bulk evaluation must wait for stable Gemini availability or a
working Mistral fallback.

Smoke evidence is isolated at `/tmp/omnirush/critic-smoke-v3.json` and
`/tmp/omnirush/truthguard-critic-smoke-v3.sqlite3`; it recorded 36 calls, 19
successful calls, 17 failed calls, and four completed questions. No live
test-set metrics were generated from this run.

### Provider limit update

- Updated Gemini 3.8 Flash to the supplied dashboard limits: 5 RPM, 250,000
  TPM, and 20 RPD.
- Updated the Mistral fallback model from the alias `mistral-small-latest` to
  the supplied `mistral-small-2603` model: 20,000 TPM and 1 request per second.
- Removed the previous unverified Mistral 500 RPD cap; the supplied dashboard
  did not show a daily request limit for that model.
- Extended router budget accounting with rolling one-second request counts and
  rolling one-minute token counts. The Mistral one-request-per-second limit is
  now enforced rather than approximated as a five-RPM limit.

### Verification

| Check | Result |
|---|---|
| `make test` | Passed: 40 tests |
| `make smoke` | Passed: offline configuration loaded |
| `make compile` | Passed |

## Task 5 — Human review sheet

### Completed

- Exported `reports/review_sheet.csv` from the frozen test split.
- Stratified sample contains exactly 30 questions: 4 each of T1–T6, 3 T0,
  and 3 T7.
- Included document IDs and titles, gold labels, winners, exact corpus
  passages, and blank reviewer fields.
- Added `scripts/compute_agreement.py`; it reports per-column agreement,
  answered/blank counts, and overall agreement. Blank fields are reported as
  pending rather than counted as disagreement.

### Verification

| Check | Result |
|---|---|
| Review sheet export | Passed: 30 rows with required 4/4/4/4/4/4/3/3 strata |
| Agreement script on blank sheet | Passed: all three columns and overall reported pending |

### Required input

- A human must fill the three reviewer columns and notes in
  `reports/review_sheet.csv`, then run:

```bash
.venv/bin/python scripts/compute_agreement.py
```

## Task 3 — Wild robustness questions (writing only)

### Completed

- Added `data/benchmark/wild.jsonl` with 20 manually phrased questions.
- Questions include indirect wording, multi-hop cases, mixed-topic cases,
  scope cases, unresolvable conflicts, a no-conflict control, and unanswerable
  questions.
- Gold labels were assigned from the corpus and conflict manifest, with source
  passage references included in each record.
- No evaluator or provider was run on this file, as required.

### Verification

| Check | Result |
|---|---|
| JSONL parse and uniqueness | Passed: 20 unique records |
| Generator phrasing check | Passed: no `(case variant ...)` phrasing |
| Gold status/type/source field check | Passed |

### Remaining

- Evaluation is intentionally deferred until the LLM critic smoke test passes
  after Gemini or Mistral credentials are added.

## Optional Phase 7 — pitch and video materials

Not started, per the user's request to keep this optional and last. If needed,
this phase will add only:

- Five-minute pitch script using the required vocabulary.
- Six-question demo script.
- Results-table narrative and honest limitations.
- Demo-video recording checklist and backup commands.

No new product features will be added in this optional phase.

## Open issues and submission gates

- Complete the 30-question human review and run
  `scripts/compute_agreement.py`.
- Run the independent second-LLM corpus audit against the conflict manifest.
- Run fair live B0/B1/B2 baselines if a provider quota is available.
- Repeat the bounded Gemini critic smoke when provider availability is stable;
  do not relabel the deterministic benchmark metrics as Gemini results.
- Verify Docker on a Docker-capable machine.

The local product, offline test suite, judge demo, API, and Streamlit UI are
demo-ready. These remaining items are evidence and packaging gates rather than
core implementation blockers.

## Wild robustness evaluation

### Completed

- Added `scripts/evaluate_wild.py` and the `make wild` command.
- Evaluated all 20 manually written wild questions offline.
- Wrote the separate report to `reports/wild_results.md`.

### Result and interpretation

- Answer accuracy: `0.3500`
- Conflict F1: `0.4348`
- Resolution-mode accuracy: `0.3000`
- Provenance correctness: `0.9000`
- False-conflict rate: `0.1000`
- Abstention recall: `0.7500`

This is a useful warning rather than a headline achievement: the deterministic
fallback is strong on the generated frozen benchmark but weaker on indirect
and mixed-topic wild wording. The wild report should be presented as an honest
robustness gap and a next improvement target, not combined with the official
test score.

The retriever also gained deterministic topic hints for indirect wording. The
complete offline 140-question test rerun remained unchanged at answer accuracy
`0.8286`, conflict F1 `0.8374`, provenance correctness `1.0`, and abstention
recall `1.0`, so the change did not regress the frozen benchmark.

### Verification

| Check | Result |
|---|---|
| `make test` | Passed: 42 tests |
| `make demo` | Passed: six cases with expected statuses |
| `make wild` | Passed: 20 questions scored and report written |
| Offline 140-question rerun | Passed: metrics unchanged from recorded fallback baseline |

## Task 1 — BGE/FAISS retrieval and cached reformulation

### Completed

- Completed `make install-ml`; the first install attempt exceeded the sandbox
  timeout during package installation, and a retry completed with the pinned
  ML dependencies already present.
- Added optional BGE embeddings using `BAAI/bge-small-en-v1.5`.
- Added FAISS inner-product dense search while retaining BM25 and RRF.
- Added one structured query-reformulation call per live question returning a
  topic and two paraphrases. The existing SQLite router cache makes repeated
  questions reuse that call.
- Added a fixed offline retrieval comparison script:
  `scripts/evaluate_retrieval.py` and `make retrieval`.

### Measurements

| Backend | Dev recall@8 | Wild answer accuracy | Wild conflict F1 | Wild mode accuracy |
|---|---:|---:|---:|---:|
| Hash + BM25 | 1.0000 (37/37) | 0.3500 | 0.4348 | 0.3000 |
| BGE + FAISS + BM25 | 1.0000 (37/37) | 0.4500 | 0.4800 | 0.3500 |

BGE removed the two hash retrieval misses in the wild set, but did not improve
dev recall because the hash path already had 37/37 source coverage. The
remaining wild failures are mostly wrong mode or conflict type, so retrieval
is no longer the only bottleneck.

### Verification

| Check | Result |
|---|---|
| `make install-ml` | Passed on retry; pinned BGE/FAISS stack installed |
| BGE model load | Passed; 384-dimensional embeddings |
| `make retrieval` | Passed; before/after JSON evidence written under `/tmp` |
| Cached reformulation test | Passed; one transport call, second call cached |

## Task 2 — provider routing and throttling

### Completed

- Changed the primary evaluation critic to Groq `qwen/qwen3.8-27b`, a model
  family different from the Groq `openai/gpt-oss-120b` synthesizer.
- Added `TRUTHGUARD_CRITIC_PROVIDER` and `TRUTHGUARD_CRITIC_CHAIN` overrides so
  Gemini can be reserved for the six-question demo and spot checks while bulk
  evaluation uses Groq Qwen with configured fallbacks.
- Recorded the observed Qwen model rate-limit headers in
  `reports/provider_limits.md`.
- Added a 1.1-second minimum Mistral request-start interval in addition to the
  rolling RPS/TPM accounting.

### Verification

| Check | Result |
|---|---|
| Groq Qwen model-list check | Passed: `qwen/qwen3.8-27b` available |
| Groq Qwen structured JSON smoke | Passed: HTTP 200; headers recorded |
| Mistral throttle configuration | Passed: 1.1-second interval configured |

## Evidence-quality correction and Task 3 quota stop

### Retrieval correction

The initial Task 1 log called any-gold-source hit@8 “recall@8.” The evaluator
now also computes actual macro document recall@8: hash **0.8243**, BGE/FAISS
**0.8784**, on 37 eligible dev questions. Both any-source hit rates remain
37/37. This is document retrieval, not semantic supporting-passage recall.
The before/after experiment used offline reformulations. The live cached
topic-plus-two-paraphrases call is implemented and mock-tested but its combined
effect with BGE has not been measured. Task 1 is therefore **partial against
the full requested live-reformulation experiment**, not fully verified.

BGE wild document overlap is **1.0000**, correcting an earlier unmeasured
copied 0.9000. Ten BGE wild conflict questions had **missing conflicts**, not
wrong detected types. Thirteen had wrong modes. Both T0 controls were false
positives: T0-only false-conflict rate **100%**, versus the legacy all-question
average of 10%. Source coverage does not prove both sides or exact supporting
passages were retrieved. No test labels, prompts, or selections were changed
based on test outcomes.

### Task 2 status: partial

Qwen model availability and a successful structured smoke were verified, and
Mistral spacing was added. However, the console-level daily Qwen limit is not
verified. The live run exposed a separate **1000 output-token/minute** Qwen
limit not captured by the 8000-token header. Local Groq counters still aggregate
models. Mistral continued returning 429 despite 1.1-second spacing. See
`reports/provider_limits.md`; quota routing is not yet validated for bulk work.

### Task 3: stopped, not complete

- Created the fixed 40-question test subset with seed `20261020`: 6 T1–T6
  each, 2 T0, 2 T7. Selection is unchanged and now committed.
- Completed the offline deterministic BGE run, 40/40.
- Attempted the live Qwen run: **7 successful answers, 18 failures, 15 not
  reached** before the shell timeout. Do not compare the successful-only live
  sample to the complete deterministic baseline.
- The initial runner incorrectly continued on rate limits. It now stops on a
  propagated quota error and rejects incompatible resume identities.
- Added a unit-tested hard cap of three actual critic requests, including
  retry/repair/fallback attempts. The earlier live run had no such cap and
  cannot be claimed compliant retroactively.
- Per-attempt retry logging and a controlled same-context/same-draft critic
  comparison remain incomplete. See `reports/critic_subset_status.md`.

### Stop reason and next action

No further live run, live wild evaluation, baseline, or corpus audit will be
started until the user confirms available Qwen/Mistral quota/access. Required
information: Qwen RPD/TPD/input-output TPM limits and remaining budget from the
existing Groq console, plus the Mistral account's current rate-limit status.
No secret values are needed. Tasks 4–8 remain uncompleted; no UI framework was
changed and no question gold labels were edited.

### Local verification after stopping live work

| Check | Result |
|---|---|
| `make test` | Passed: 50 tests; one existing Starlette deprecation warning |
| `make compile` | Passed |
| `git diff --check` | Passed |
| `make retrieval` | Reran both backends; document recall and hit-rate definitions corrected |

The new request-budget test counts retry transport attempts, and evidence tests
distinguish cache hits/fallbacks, avoid cross-role fallback inflation, and reject
legacy output rather than mixing experimental modes. No new live API calls
were made after the quota blocker was identified.
