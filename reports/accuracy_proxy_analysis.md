# TEST answer-proxy analysis

This is a diagnostic report over the frozen v2 TEST split. It does not tune detector rules, labels, retrieval, or prompts. Both systems use the same 146 questions and the same deterministic HashEmbedder evaluation path; the only comparison is the measured full system versus the recorded `no_critic` ablation.

## Metric definitions

- **Answer proxy:** the existing numeric/substring score for a non-null gold answer, exact `not_in_corpus` for T7, and exact abstained status for T6. It is retained for historical comparability.
- **Status-correct answer rate:** for resolved rows, the same answer proxy; for conditional, abstained, no-conflict, and not-in-corpus rows, exact final-status correctness. This is computed identically for both systems and does not claim semantic entailment.
- Intervals are 1,000-sample question-level bootstrap 95% CIs. Values are deterministic/offline; no provider answered these rows.

## By gold type and gold status

| Type | Gold status | n | Full answer proxy | No-critic answer proxy | Full status-correct | No-critic status-correct | Full predicted statuses | No-critic predicted statuses |
|---|---|---:|---:|---:|---:|---:|---|---|
| T0 | no_conflict | 18 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | no_conflict:18 | no_conflict:18 |
| T1 | resolved | 17 | 0.7647 | 1.0000 | 0.7647 | 1.0000 | not_in_corpus:4, resolved:13 | no_conflict:17 |
| T2 | conditional | 18 | 1.0000 | 1.0000 | 0.7222 | 0.0000 | conditional:13, no_conflict:5 | no_conflict:18 |
| T3 | resolved | 36 | 0.2222 | 0.8611 | 0.2222 | 0.8611 | abstained:23, not_in_corpus:5, resolved:8 | no_conflict:36 |
| T4 | resolved | 17 | 0.7059 | 0.7647 | 0.7059 | 0.7647 | not_in_corpus:5, resolved:12 | no_conflict:17 |
| T5 | conditional | 21 | 0.7619 | 1.0000 | 0.7619 | 0.0000 | conditional:16, not_in_corpus:5 | no_conflict:21 |
| T6 | abstained | 6 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | abstained:6 | no_conflict:6 |
| T7 | not_in_corpus | 13 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | not_in_corpus:13 | no_conflict:13 |

## Overall TEST comparison with bootstrap CIs

| System | n | Answer proxy (95% CI) | Status-correct answer (95% CI) |
|---|---:|---:|---:|
| full_system | 146 | 0.7123 [0.6370, 0.7808] | 0.6781 [0.5890, 0.7534] |
| no_critic | 146 | 0.8082 [0.7534, 0.8699] | 0.5411 [0.4589, 0.6233] |

## Conflict-disclosure interpretation

- `full_system` on T2/T5/T6 conditional-or-abstention rows (n=45): answer proxy `0.8889` [0.7778, 0.9778], status-correct answer `0.7778` [0.6444, 0.8889].
- `no_critic` on T2/T5/T6 conditional-or-abstention rows (n=45): answer proxy `0.8667` [0.7556, 0.9556], status-correct answer `0.0000` [0.0000, 0.0000].

The higher `no_critic` micro answer proxy is not evidence that conflict checking is harmful: the no-critic path scores 0.0000 conflict F1 and 0.1233 resolution-mode accuracy in the frozen ablation. The old proxy can reward a value-containing blended answer on a conflict row while failing to credit a correct conditional or abstained final status unless its special T6/T7 rule applies. The status-correct metric makes the final behavior comparison explicit, while preserving the old proxy rather than replacing it.

This report does not tune on TEST or wild and does not change frozen gold labels.
