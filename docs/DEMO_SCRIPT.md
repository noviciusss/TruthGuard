# TruthGuard Demo Script

## Goal and preparation

Show how a local prototype exposes disagreement in a synthetic policy corpus.
Use Python 3.11.2 and follow [setup](../README.md) first:

```bash
make install
make test
TRUTHGUARD_OFFLINE=true make demo
TRUTHGUARD_OFFLINE=true make ui
```

Open `http://127.0.0.1:8501`. Use
[the scripted demo output](../reports/demo_output.md) as a backup. These are
walkthrough instructions; packaging validation did not execute the installs,
regenerate this artifact, or verify UI/container startup.

## Opening

> Retrieved policy documents can disagree because an amendment changed a rule,
> an exception has a narrower scope, or two official sources conflict.
> TruthGuard aims to make that disagreement visible, show its evidence and
> trust factors, and abstain when there is no defensible winner. This demo uses
> fictional documents and a deterministic offline critic, not a live LLM critic.

## 1. Supersession

Question: `What is the hospitalization waiting period for the Standard plan?`

Inspect the old 30-day policy, newer 45-day amendment, T1 classification,
supersession relationship, and resolved answer.

> Here we can inspect both positions and the amendment relationship that
> explains the chosen rule.

## 2. Scope

Question: `Is the co-payment different for a member aged 60 or above?`

Inspect the 10% standard rule, 20% senior-member rule, T2 classification, and
conditional answer.

> These values apply to different populations. A conditional answer preserves
> the distinction instead of selecting a single percentage for everyone.

## 3. Exception

Question: `Is prior authorization required for every hospital admission?`

Inspect the planned-admission requirement, emergency exception, T5
classification, and 24-hour notification condition.

> The narrower exception is part of the answer. We want the evidence for both
> the general rule and its exception to be visible.

## 4. Abstention

Question: `For a Standard inpatient room, the evidence gives two different caps effective on the same date. Is either cap authoritative?`

Inspect the two new same-authority circulars, their identical effective date,
the 1% versus 2% room-rent-cap passages, T6 classification, and abstained
answer. This is a genuine whole-corpus T6: no third document or later
amendment settles the fact.

> Both cited circulars are equally authoritative and effective on the same date.
> Since no other document resolves the room-rent-cap fact, TruthGuard abstains
> instead of selecting 1% or 2%.

## 5. Not in corpus

Question: `Does Aurelia cover hearing-aid batteries after a routine replacement?`

Inspect the `not_in_corpus` status.

> Missing evidence and contradictory evidence are different situations. This
> case is intended to demonstrate the first.

## Close with evidence boundaries

> This is an inspectable prototype, not proof of production accuracy. The
> corpus is synthetic and the main benchmark is templated from shared facts.
> Historical wild answer-proxy accuracy improved from 0.35 to 0.45 with
> BGE/FAISS retrieval, but remained weak. The later fact-level conflict fix
> removed observed T0 false positives, but wild accuracy fell from 0.45 to 0.40
> and wild conflict recall fell. These are measured trade-offs, not a general
> robustness improvement. All these runs used offline reformulations and
> deterministic criticism. Document-level provenance checks document IDs or citation presence,
> not semantic support. The quota-limited fixed40 LLM-critic experiment completed
> only seven live answers, so the partial live run is not comparative results.

If asked about lineage, explain that the historical full test metrics used a
deterministic critic even with live synthesis. The partial fixed40 run used
Groq Qwen for criticism and Groq GPT-OSS for synthesis, not a validated Gemini
or Mistral critic. Avoid claiming that a configured provider served a result.

Point to [the submission evidence](../SUBMISSION.md),
[wild results](../reports/wild_results.md), and
[fixed40 status](../reports/critic_subset_status.md). If comparing the UI's
Naive RAG and TruthGuard outputs, describe only the observed example; do not
present it as a completed comparative live benchmark.
