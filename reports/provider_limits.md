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

The endpoint exposes the request and token limits but does not label the
request window as daily in the header name. The configured guard therefore
records the observed 1000-request limit and 8,000-token limit without claiming
an undocumented time window. The provider dashboard/headers should be checked
again before a larger run.

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
starts, in addition to the rolling request/token budget checks, to reduce
free-tier 429 bursts.
