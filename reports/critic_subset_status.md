# Fixed Test-Subset Critic Evaluation — Blocked

## Selection

- File: `data/benchmark/eval_subset_40.jsonl`.
- Seed: `20261020`.
- T1–T6: 6 questions each; T0 and T7: 2 each.
- All 40 questions originate in the frozen test split.
- Selection was made before looking at run outcomes and has not been changed.
- The subset was committed after the initial live attempt, not before it;
  future runs must reuse this committed selection.

## Completed baseline

The offline deterministic-critic run completed 40/40 using BGE + FAISS. There
was no LLM critic provider and no live synthesizer. This differs upstream from
the live experiment, so it is an end-to-end baseline, not a controlled
critic-only ablation.

| Measure | Deterministic result |
|---|---:|
| Conflict F1 | 0.8824 |
| Blended-answer proxy | 0.0000 |
| T6/T7 combined abstention recall | 1.0000 |
| T0-only false-conflict rate | 1.0000 (2/2) |
| Numeric/substring answer proxy | 0.8500 |

The zero blended-answer proxy is not an independent semantic judgment; see
`bench/metrics.py` for its status/conflict-based definition. Document provenance
measures document-ID overlap, not supporting-span correctness.

## Partial live run

- 7 successful answers out of the intended 40.
- 18 question-level failure records.
- 15 questions not reached before the 20-minute shell timeout.
- No live wild evaluation was started.
- No live baseline or corpus audit was started after this blocker.

| QID | Actual reformulation/synthesis provider and model | Actual critic provider and model | Successful logical critic stages | Recorded schema-repair events | Outcome |
|---|---|---|---:|---:|---|
| t0-004 | groq / openai/gpt-oss-120b | groq / qwen/qwen3.8-27b | 2 | 0 | no_conflict |
| t1-017 | groq / openai/gpt-oss-120b | groq / qwen/qwen3.8-27b | 3 | 0 | resolved |
| t1-024 | groq / openai/gpt-oss-120b | groq / qwen/qwen3.8-27b | 2 | 0 | no_conflict |
| t2-002 | groq / openai/gpt-oss-120b | groq / qwen/qwen3.8-27b | 2 | 0 | no_conflict |
| t2-024 | groq / openai/gpt-oss-120b | groq / qwen/qwen3.8-27b | 2 | 0 | no_conflict |
| t3-002 | groq / openai/gpt-oss-120b | groq / qwen/qwen3.8-27b | 3 | 0 | resolved |
| t3-018 | groq / openai/gpt-oss-120b | groq / qwen/qwen3.8-27b | 3 | 0 | resolved |

These are partial outcomes, not correctness claims. Several conflict questions
were incorrectly answered as `no_conflict`. No aggregate live accuracy/F1 is
reported: the seven available successes are an availability-biased sample.

The router log recorded 27 successful Qwen critic stage records, 5 failed Qwen
critic records, and no schema-repair events. Some successful stages belong to
questions that later failed. Internal HTTP retries were not individually
logged, so the initial experiment does **not** prove first-attempt parse rates
or compliance with a three-actual-request limit. The old fallback counter also
mistook different role models for fallbacks; it must not be used as evidence.
Nine Mistral fallback records (8 generation, 1 synthesis) all failed.

## Blocker

Groq reported `OTPM: Limit 1000` for Qwen, with requests estimated at 1182 and
1115 output tokens rejected as too large. Provider-wide local TPM guards also
interfered with the run. Mistral returned 429 despite the 1.1-second interval.
The initial runner continued after quota failures; that was an error. The
saved runner now stops at the first propagated quota/rate-limit failure.

Raw diagnostics remain in the local container at
`/tmp/omnirush/critic-llm-40.jsonl` and its adjacent SQLite database. These are
not portable repository artifacts. This report contains only redacted,
non-secret summaries. Do not copy raw private diagnostics into the repository.

## Local safeguards added after the run

- Frozen subset generation refuses to overwrite a changed selection.
- Resuming rejects mismatched modes, configuration, questions, or relevant
  environment overrides instead of silently combining experiments.
- Failed questions retain their available call records.
- Cache hits are distinct from fresh schema-valid stage responses.
- Fallback counts are critic-stage-specific, not cross-role model changes.
- A shared three-request critic budget now bounds actual transport attempts,
  including retries/repairs/fallbacks. This guard is unit-tested but was not
  present in the partial live run above.

## Required before resuming

1. Confirm Qwen per-model RPD, TPD, input/output TPM and remaining quota from
   the Groq account console. Do not supply credentials in a report or chat.
2. Resolve the Mistral 429 access/quota issue in the existing account.
3. Add model-specific pacing and a bounded output policy that fits the verified
   limit; verify structured schemas without tuning on test answers.
4. Log each physical attempt, including retries, so per-question first-try
   parsing and request counts can be audited.
5. Hold retrieved contexts and draft answers constant for the controlled critic
   comparison. Preserve the original partial run separately; do not merge it
   into a differently configured resumed experiment.
