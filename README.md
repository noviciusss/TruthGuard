# TruthGuard

TruthGuard is an offline-first prototype for question answering over a
deliberately inconsistent, **synthetic Aurelia Health** policy corpus. It
retrieves competing evidence, checks draft claims, exposes conflicts and trust
factors, and resolves, answers conditionally, or abstains.

The local interfaces are **Streamlit** and **FastAPI**. Start with the offline
walkthrough; evaluation evidence and its limitations are summarized below.

- [Project guide](docs/PROJECT_GUIDE.md): setup, components, and remaining work
- [Architecture](docs/ARCHITECTURE.md): deterministic and LLM paths
- [Demo script](docs/DEMO_SCRIPT.md): judge walkthrough
- [Submission](SUBMISSION.md): pitch and evidence boundaries

## Setup on Linux

Use Python **3.11.2** (pinned in `.python-version`), its `venv` module, GNU Make,
and Git. Locks target CPython 3.11.2 on Linux x86_64; other platforms have not
been validated. Run commands from the repository root:

```bash
python3 --version  # expected: Python 3.11.2
make install
# Optional local configuration; do this only if .env does not already exist:
test -e .env || cp .env.example .env
```

`make install` creates `.venv`, installs the pinned installer `pip==26.2.1`,
installs **`requirements.lock`**, and runs `pip check`. The lock includes the
runtime and pytest dependency closure, including Streamlit/PyVis transitives.
The `.txt` files describe direct requirements; the `.lock` files are the install
inputs. No global Python install is needed.

Installation requires access to package indexes or a pre-populated local
wheelhouse. **Offline-first describes execution after setup**, not downloading
dependencies. These are version locks, not artifact-hash locks; base-image tags
and Debian package repositories are also not immutable snapshots.

### Optional dependencies

```bash
make install-ml             # CPU Torch, sentence-transformers, BGE/FAISS stack
make install-orchestration  # LangGraph adapter
```

Each target installs its optional lock **together with `requirements.lock`**,
so shared dependency versions stay pinned. The ML lock uses the PyTorch CPU
index and a large CPU Torch wheel; it does not install CUDA dependencies.
Model weights for `BAAI/bge-small-en-v1.5` are a separate download and are not
bundled or revision-locked. Offline execution defaults to the deterministic
hash embedder without needing those weights. The manual state machine works
without LangGraph.

## Offline checks

The single test command, after installing dependencies, is:

```bash
make test
```

It needs no provider credentials, network connection, or model download.
Additional local checks are `make smoke` and `make compile`.

## Run locally

Force offline mode explicitly, including when an existing `.env` has live
settings:

```bash
TRUTHGUARD_OFFLINE=true make ui
# Open http://127.0.0.1:8501
```

For the API, in a separate terminal:

```bash
TRUTHGUARD_OFFLINE=true make api
# Open http://127.0.0.1:8000/docs
```

The UI exposes citations, claim verdicts, competing document positions, trust
breakdowns, graph relationships, and an execution trace. A scripted walkthrough
is available with `make demo` (writes `reports/demo_output.md`). This is a
demonstration, not an independent benchmark result.

Provider mode requires credentials in `.env` and `TRUTHGUARD_OFFLINE=false`.
See `config.yaml` for role chains. Live synthesis and an LLM critic are distinct
from the offline deterministic path; enabling live mode does not establish
which provider actually succeeded. Keep `.env`, API keys, caches, and raw
provider output out of version control.

## Container build and local deployment

The Dockerfile uses Python 3.11.2, installs Make/Git and the same core lock, and
includes an offline test build step. It packages the synthetic inputs and
Markdown evidence, without copying the local `.env`, provider database, model
cache, or raw live-evaluation JSONL files. The default command starts Streamlit.

On a Docker-capable machine:

```bash
docker build -t truthguard .
docker run --rm --network none truthguard make test PYTHON=python
docker run --rm -e TRUTHGUARD_OFFLINE=true -p 127.0.0.1:8501:8501 truthguard
```

Open `http://127.0.0.1:8501`. To deploy the API locally instead:

```bash
docker run --rm -e TRUTHGUARD_OFFLINE=true -p 127.0.0.1:8000:8000 truthguard \
  python -m uvicorn truthguard.api:app --host 0.0.0.0 --port 8000
```

These are local deployment instructions; no public service deployment is
verified. Docker is unavailable in the packaging environment, so **the image
build, build-time tests, and container startup have not been run**.

## Evidence and limitations

- **Synthetic, templated benchmark:** 35 fictional documents and 180 generated
  questions (40 development, 140 test). Questions and documents share a factsheet
  and templates. This is not independent real-world validation.
- **Historical deterministic results:** the recorded 140-question run used live
  Groq synthesis with a deterministic critic. Reported answer-proxy accuracy
  `0.8286` and conflict F1 `0.8374` are historical, not fresh measurements of
  ongoing changes or evidence of LLM-critic quality. The offline B0/B1/B2 table
  is not a completed live-model comparison.
- **Wild before/after:** the existing 20-question offline comparison records
  answer-proxy accuracy **0.35 → 0.45** for hash/BM25 versus BGE/FAISS/BM25
  (conflict F1 `0.4348 → 0.4800`). These are historical measurements with the
  deterministic critic and offline reformulations. A subsequent DEV-selected
  fact-level conflict fix (BGE held fixed) reduced TEST T0 false positives from
  **15/18 to 0/18**, and wild T0 false positives from **2/2 to 0/2**. It also
  reduced wild answer proxy accuracy **0.45 → 0.40** and wild conflict recall
  **0.3750 → 0.3125**. This is a conservative precision trade-off, not an overall
  robustness gain. See [the before/after evidence](reports/false_conflicts.md).
- **Provenance is document-level:** `provenance_correctness` checks overlap
  with gold document IDs on conflict questions, and citation presence otherwise.
  It does not measure semantic support, correct spans, or complete coverage of
  competing evidence. Numeric/substring answer matching and the blended-answer
  proxy also need human interpretation.
- **Quota-limited fixed40 subset:** the frozen 40-question selection has six
  questions each for T1–T6 and two each for T0/T7. An offline BGE deterministic
  run completed 40/40. The live experiment completed only 7/40, with 18 failures
  and 15 unreached questions. Successful calls used Groq Qwen for the critic
  and Groq GPT-OSS for synthesis; they do not validate Gemini/Mistral lineage.
  The partial live run is availability-biased and **not comparative results**.
  Upstream retrieval/drafting also differed, preventing a critic-only ablation.
- The [programmatic corpus audit](reports/corpus_audit_programmatic.md) ran
  offline: 100/200 unique questions passed applicable mechanical checks and
  100 remained unverifiable. Seven documents failed version recovery. A notice
  has internally inconsistent annual limits, and whole-corpus T6 applicability
  needs adjudication. No corpus or question gold was silently changed.
- The seven corrupted-version documents are explicitly retained as unknown
  version with zero metadata confidence: `POL-2025-V2`, `AMD-2025-07`,
  `AMD-2026-04`, `CIR-2025-08-A`, `FAQ-2024-01`, `FAQ-2026-02`, and
  `NOTICE-2024-01`. Supersession can still use explicit dates/edges; version
  identity is not fabricated from the manifest.
- Human semantic label review, audit adjudication, a controlled LLM-critic
  comparison, and clean-install/container runtime validation remain evidence
  gaps. No live evaluations resume until the required offline gates are met.

See [evaluation results](reports/results.md), [wild results](reports/wild_results.md),
and [fixed40 status](reports/critic_subset_status.md) for historical details.

### Packaging verification boundary

Core and combined core+ML+orchestration lock resolution passed pip
`--dry-run --ignore-installed` on Linux x86_64 / Python 3.11.2. This validates
dependency resolution, not an actual clean installation or optional runtime.
The existing virtualenv passes the offline suite but `pip check` reports
missing `ipython`, `altair`, `gitpython`, `pandas`, `pydeck`, and `rich`;
the new core lock explicitly includes them. The install targets have not been
executed in a fresh virtualenv, and UI startup in that environment is unverified.
