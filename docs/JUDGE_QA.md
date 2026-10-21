# Judge Q&A

## 1. Is the corpus real?

No. It is a fictional Aurelia Health corpus. It is intentionally synthetic so
the conflict types and evidence chains are inspectable and reproducible.

## 2. Is the benchmark independent?

No. The same team generated the benchmark from shared facts and templates.
Human review agreement is still pending. We report this as a controlled offline
evaluation, not independent validation.

## 3. Why is no_critic answer proxy higher than TruthGuard?

The deterministic TEST answer proxy is not semantic accuracy. It rewards
numeric/substring matches and special statuses. The no-critic path measured
answer proxy 0.8082 but conflict F1 0.0000 and mode accuracy 0.1233. A second
status-correct answer rate gives 0.6781 for TruthGuard versus 0.5411 for
no_critic, because it credits correct conditional/abstained behavior.

## 4. Did you tune on TEST?

No. Conflict detector changes were selected on DEV before the v2 frozen rerun.
The v2 benchmark labels and hashes were frozen before TEST metrics and
ablations. The proxy analysis is diagnostic only and did not change rules.

## 5. What does the supersession ablation show?

Removing the supersession graph reduced deterministic TEST conflict F1 from
0.8835 to 0.6782 and mode accuracy from 0.6781 to 0.4589. It also changed 33
public outputs. This is a component ablation on 146 TEST questions, not a live
LLM comparison.

## 6. Why add T6 late?

The original corpus did not contain 12 defensible current whole-corpus T6
questions. Rather than fabricate evidence, we added an additive v2 revision:
six new fact keys, two equal-authority same-date documents per key, and 12 new
T6 questions. Existing v1 labels stayed unchanged and v2 hashes are recorded.

## 7. What is T6?

T6 is a same-authority unresolved conflict. In v2 each pair has different
values, identical effective/issued dates and authority, no amendment edge, and
no third document settling the fact. TruthGuard abstains.

## 8. Why report macro and micro metrics?

TEST is T3-dominant: 36 of 146 rows are T3. Micro metrics reflect the actual
question mix; macro metrics give each present type equal weight. Both are
reported so the pitch does not hide the composition effect.

## 9. What does provenance correctness measure?

Only document-level ID overlap on conflict questions and citation presence on
other questions. It does not verify semantic entailment, exact supporting spans,
or complete competing evidence.

## 10. Why use free-tier models?

The optional LLM path was designed around available provider roles and strict
request/token budgets. Provider/model identity is recorded from successful
responses, not configured role names. In this final session no v2 live call was
made because credentials were unavailable, so there is no live model claim.

## 11. Was the live critic evaluated?

Not for v2. D1 was gated before the first request: 0/40 completed and 40 were
unreached because no provider credential was available. The earlier v1 7/40
partial run had different contexts and is explicitly non-comparative.

## 12. Did you test B0/B1 live?

No. D2 was not started after the live gate failed. The compare-mode UI example
is a deterministic local observation only, not a live baseline benchmark.

## 13. What are the seven unknown versions?

Seven intentionally corrupted document headers remain `version=null` with
metadata confidence zero. The loader does not copy manifest values into runtime
metadata. Explicit effective dates and graph edges may still support
supersession reasoning.

## 14. Does the system support as-of questions?

No, not as a user-facing contract. Internal effective-date reasoning exists for
supersession, but an as-of-date query feature was not implemented or evaluated.

## 15. What should we take away?

TruthGuard demonstrates an inspectable verification layer: it can preserve
competing evidence, distinguish scope and exceptions, resolve supersession, and
abstain on genuine ties. The honest boundary is equally important: this is a
synthetic, same-team benchmark with proxy metrics, weak wild coverage, pending
human agreement, and no completed v2 live-provider evaluation.
