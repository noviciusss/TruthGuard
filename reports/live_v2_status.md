# V2 live evaluation status

## Gate result

No live provider call was made in this session. The optional quota block was
empty, and the process environment had no usable credentials:

```text
GROQ_API_KEY=missing
MISTRAL_API_KEY=missing
GEMINI_API_KEY=missing
OPENROUTER_API_KEY=missing
```

Because there was no credential with which to receive a response, no
`x-ratelimit-*` headers or new 429 evidence could be discovered. The run was
stopped before the first request rather than pretending that a quota was
available or retrying a blocked path.

## D1 — fixed-40 v2 critic comparison

| Item | Result |
|---|---|
| Questions requested | 40 |
| Completed | 0 |
| Failed provider calls | 0 |
| Unreached | 40 |
| Actual provider/model | none |
| First-try parse / repair / fallback | not exercised |
| Live metrics | not measured |

The fixed v2 file is `data/benchmark/eval_subset_v2_40.jsonl`, regenerated with
seed `20261020` and the existing 2/6/6/6/6/6/6/2 stratification. No LLM-critic
comparison is claimed.

## D2 — live B0/B1

Not started because D1's provider gate was unavailable. Requested, completed,
failed, and unreached counts are all `0`; no provider/model answered.

## D3 — live wild

Not started because no quota-bearing credential was available after the D1/D2
gate. No live wild result is claimed.

## Historical evidence kept separate

The prior v1 partial run remains non-comparative and is not merged into v2:
Qwen produced 7/40 successful answers before quota/failure interruption,
18 records failed, 15 questions were unreached, and Mistral returned HTTP 429.
Those requests used different upstream contexts and do not exercise the v2
fixed subset.
