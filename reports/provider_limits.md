# Provider Limit Verification

Updated: 2026-10-20

## Groq critic model

The Groq model list endpoint reported the available alternate-family model:

```text
qwen/qwen3.8-27b
```

A schema-valid JSON smoke request was sent to the Groq OpenAI-compatible chat
endpoint using that model. The response headers reported:

| Header | Observed value |
|---|---:|
| `x-ratelimit-limit-requests` | `1000` |
| `x-ratelimit-limit-tokens` | `8000` |
| `x-ratelimit-remaining-requests` | `999` |
| `x-ratelimit-remaining-tokens` | `7959` |
| `x-ratelimit-reset-requests` | `1m26.4s` |
| `x-ratelimit-reset-tokens` | `307ms` |

The header names alone do not establish all per-model daily quotas. The
configured `rpd_limit: 1000` is a **local conservative guard**, not a newly
verified daily model entitlement. The router also currently aggregates Groq
usage across roles/models; it must become model-specific before a fair bulk
run. Confirmation of Qwen RPD, TPD and output-token limits from the account
console is still required.

### Live subset blocker

During the fixed-subset run, Groq explicitly reported a separate Qwen
**output tokens per minute (OTPM) limit of 1000**. Requests with estimated
outputs of 1182 and 1115 tokens were rejected as too large. The 8000-token
header did not establish this separate output limit. Mistral returned HTTP 429
despite serialized 1.1-second spacing. No further live evaluation, baseline,
or audit calls are authorized by this run's evidence until these quota issues
are resolved.

## Gemini

The configured Gemini 3.8 Flash dashboard limits are:

- 5 RPM.
- 250,000 TPM.
- 20 RPD.

Gemini is reserved for the six-question demo and spot checks, not the bulk
critic evaluation.

## Mistral

The configured `mistral-small-2603` limits are:

- 20,000 TPM.
- 1 request per second.
- No daily request limit was shown in the supplied dashboard.

The router now enforces a 1.1-second minimum interval between Mistral request
starts within one router process, in addition to the request/token budget
checks, to reduce free-tier 429 bursts. The current minute counters use fixed
UTC-minute buckets, not fully rolling token windows; no cross-process interval
guarantee is implemented. The observed Mistral 429s show that spacing alone
has not resolved provider access/quota restrictions.
