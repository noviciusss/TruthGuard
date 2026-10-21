# TruthGuard Architecture

## Design principle

TruthGuard separates answer drafting from verification so competing passages
can remain visible instead of being silently blended. It is a prototype over
a small synthetic policy corpus; the architecture is not a guarantee that
every claim or conflict is detected.

## End-to-end flow

```text
Question
   ↓
BM25 + dense retrieval + reciprocal rank fusion
   ├─ conflict-seeking reformulations
   └─ supersession-graph neighbors
   ↓
Passage-grounded draft and citations
   ↓
Critic: deterministic checks OR optional structured LLM stages
   ↓
Evidence annotations + graph relationships + trust factors
   ↓
Resolver
   ↓
Answer, competing positions, citations, and execution trace
```

## Retrieval and drafting

Section-aware chunks retain character offsets. BM25 and dense rankings are
merged with reciprocal rank fusion. Graph neighbors and reformulations aim
to surface governing amendments and exceptions as well as the original rule.

Offline execution defaults to deterministic hash embeddings, requiring no
model files. Optional BGE small + FAISS retrieval requires the CPU ML lock and
separately provisioned model weights. Those weights are not bundled or pinned
to an immutable revision. Retrieving one gold document does not prove all
competing documents or the supporting passages were retrieved.

The synthesizer drafts from retrieved passages with inline citations. Offline
drafting uses a deterministic fallback. Live drafting uses configured provider
chains; a live draft does not imply a live critic.

## Two critic paths

### Deterministic

The offline critic uses domain-specific patterns, extracted values, evidence
spans, and graph relationships. It produces claim verdicts and conflict
annotations without model calls. This is the critic behind the historical
140-question headline figures, even where synthesis was live.

### Optional LLM

The structured LLM path attempts:

1. Atomic claim decomposition with supported/contradicted/unsupported verdicts.
2. Pairwise conflict detection and T1–T6 classification.
3. Self-critique of proposed conflicts to reduce false positives.

Deterministic annotations and trust arithmetic remain separate. Provider
availability, response schemas, request budgets, and fallback behavior affect
the live path. Consult `config.yaml` for role chains and actual call records
for successful provider/model identity. The partial fixed40 experiment used
Groq Qwen criticism and Groq GPT-OSS synthesis; it does not validate a
Gemini/Mistral deployment or establish cross-provider independence. Mocked
tests establish local mechanics, not semantic quality.

## Taxonomy and decisions

| Type | Meaning | Intended handling |
|---|---|---|
| T0 | No real conflict | Answer normally |
| T1 | Temporal or supersession conflict | Prefer valid governing source |
| T2 | Population/scope difference | Answer conditionally |
| T3 | Numeric/version conflict | Use authority and governing version |
| T4 | Definition/lookback conflict | Explain governing definition |
| T5 | Implicit exception | Preserve scopes and conditions |
| T6 | Same-authority unresolved conflict | Abstain |
| T7 | Topic absent from corpus | Report missing evidence |

Trust factors combine recency, authority, specificity, corroboration, and
metadata confidence. They are inspectable heuristics, not calibrated
probabilities. The resolver can emit `resolved`, `conditional`, `abstained`,
`not_in_corpus`, or `no_conflict` for an ordinary supported answer.

## Runtime and interfaces

The default orchestrator is a manual state machine, with an optional LangGraph
adapter. FastAPI exposes the query pipeline; Streamlit exposes claim verdicts,
citations, graph relationships, trust factors, and trace. Core, ML, and
orchestration dependency closures are version-pinned separately. Optional
locks are installed alongside core pins. See the [README](../README.md) for
setup and local/container deployment commands.

## Evaluation boundaries

- The v2 corpus is synthetic (47 fictional documents), and the 190-question
  benchmark is templated from shared facts by the same team that built the
  system. Human review agreement is pending. The factsheet has 20 distinct
  keys; benchmark coverage is T0=`renewal_grace`, T1=`waiting_period`,
  T2=`copay`, T3=`annual_limit`/`claim_deadline`, T4=`pre_existing_lookback`,
  T5=`preauthorization`, six new T6 tie keys, and T7=`not_in_corpus`.
  DEV, TEST, wild, and the fixed v2 subset each contain 8 distinct
  benchmark keys/classes. TEST is T3-dominant (36/146), so both micro and macro
  metrics are reported. This does not establish general real-world robustness.
- The historical offline wild comparison records answer-proxy accuracy
  **0.35 → 0.45** after switching hash/BM25 to BGE/FAISS/BM25. Both runs used
  deterministic criticism and offline reformulations; it does not measure live
  LLM gains. The subsequent fact-level conflict fix (BGE held fixed) removed
  observed TEST T0 false positives (15/18 → 0/18) and wild T0 false positives
  (2/2 → 0/2), but wild answer proxy accuracy fell 0.45 → 0.40. Full results,
  including recall costs, are in [the offline before/after report](../reports/false_conflicts.md).
- The provenance metric measures document-ID overlap (or citation presence
  on non-conflict questions), **not semantic support** or supporting-span
  correctness. Answer and blended-answer scores also use proxies.
- The v2 wild set has 22 questions and deterministic conflict F1 `0.5600`,
  compared with TEST `0.8835`; it is a weak, small robustness check.
- The frozen deterministic path is the measured path for offline retrieval,
  drafting, criticism, conflict typing, trust scoring, metadata inference,
  supersession graph behavior, and resolution. `no_self_critique` and
  `no_conflict_seeking_expansion` are LLM-path-only and were not measured on
  TEST.
- Seven corrupted versions are retained as unknown with zero confidence. The
  user-facing system does not support an as-of-date query, even though internal
  effective-date reasoning exists.
- The quota-limited fixed40 selection has a completed offline deterministic
  baseline but only 7/40 successful live answers. The partial live run is not
  comparative results: availability bias and different upstream drafts/contexts
  prevent a controlled critic comparison.
- Clean lockfile installs, optional-stack runtime, and Docker build/startup
  remain unverified in the packaging pass. Resolver dry-runs do not prove them.

Historical evidence: [results](../reports/results.md),
[wild report](../reports/wild_results.md), and
[fixed40 status](../reports/critic_subset_status.md).
