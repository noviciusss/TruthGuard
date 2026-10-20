# TruthGuard Architecture

## 1. Design principle

The central design decision is to separate **answer generation** from
**adversarial verification**. A synthesizer is allowed to draft a useful
answer, but a separate critic path asks whether every claim is supported,
whether other documents disagree, and whether a source is stale or scoped
differently.

## 2. End-to-end flow

```text
User question
    │
    ▼
Retriever ── BM25 + deterministic dense fallback + rank fusion
    │
    ├── conflict-seeking reformulations
    └── supersession-graph neighbors
    │
    ▼
Synthesizer ── passage-only draft with citations
    │
    ▼
Critic Call A ── atomic claims and evidence verdicts
    │
    ▼
Critic Call B ── pairwise conflict detection and T1–T6 classification
    │
    ▼
Critic Call C ── self-critique of proposed conflicts
    │
    ▼
Deterministic annotations ── spans, graph facts, winner, trust scores
    │
    ▼
Resolver ── resolved / conditional / abstained / not-in-corpus
    │
    ▼
Answer with citations, conflicts, trust breakdown, and trace
```

## 3. Retrieval

The retriever indexes section-aware chunks with exact character offsets. It
combines lexical and dense-fallback scores, then applies reciprocal rank
fusion. The original question receives priority, while reformulations search
for amendments, exceptions, circulars, or other governing documents.

The supersession graph adds related documents and partial section relationships
so a query about a current rule can still surface the older position that it
replaced.

## 4. Synthesis

The synthesizer drafts only from retrieved passages and emits inline chunk
citations. It is not trusted as the final authority. Its output is an input to
the critic.

## 5. Critic

### Call A: claims

The draft is decomposed into atomic claims. Each claim receives a
`supported`, `contradicted`, or `unsupported` verdict, supporting and
contradicting evidence references, and a rationale.

### Call B: conflicts

Retrieved passages are clustered by topic and compared pairwise. The critic
looks for explicit numeric disagreement, implicit contradiction, scope
differences, staleness, and supersession. It assigns T1–T6 types.

### Call C: self-critique

Proposed conflicts are attacked for false positives. A conflict can be dropped
if the positions are actually scoped differently, unrelated, or properly
resolved by supersession.

The live architecture uses Gemini first for these calls and Mistral as a
fallback. The deterministic path remains available for offline tests and for
the complete reproducible benchmark.

## 6. Conflict taxonomy

| Type | Meaning | Typical decision |
|---|---|---|
| T0 | No real conflict | Answer normally |
| T1 | Temporal or supersession conflict | Prefer valid later source |
| T2 | Scope or population conflict | Answer conditionally |
| T3 | Numeric/version conflict | Prefer governing current source |
| T4 | Definition or lookback conflict | Resolve through version/authority |
| T5 | Implicit exception conflict | State both scopes/conditions |
| T6 | Same-authority unresolved conflict | Abstain |
| T7 | Question absent from corpus | Report not in corpus |

## 7. Trust scoring

Trust scores are deterministic and inspectable. They combine recency,
authority rank, specificity, corroboration, and metadata confidence. The score
is not presented as an unexplained probability. The UI exposes the breakdown so
a reviewer can understand why a document won or why the system declined to
choose.

## 8. Resolver behavior

The resolver turns critic output into one of four user-facing outcomes:

- `resolved`: one supported governing answer wins.
- `conditional`: multiple positions are valid under different scopes.
- `abstained`: evidence conflicts without a defensible winner.
- `not_in_corpus`: the evidence base does not answer the question.

## 9. Why this beats ordinary RAG

Naive RAG optimizes for relevance and fluency. TruthGuard adds the missing
verification layer. Its primary success is avoiding dangerous false certainty:

- It reports a conflict instead of blending values.
- It identifies stale documents instead of treating all passages equally.
- It preserves exceptions instead of overgeneralizing.
- It abstains when the corpus cannot justify a decision.
