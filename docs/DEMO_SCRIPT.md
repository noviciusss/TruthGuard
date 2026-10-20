# TruthGuard Demo Script

## Goal

Demonstrate in five minutes that TruthGuard detects and explains document
disagreement instead of returning a fluent blended answer.

## Preparation

```bash
make test
make demo
make ui
```

Open `http://127.0.0.1:8501`. If the UI is unavailable, use
`reports/demo_output.md` as the backup artifact.

## Opening statement

> Ordinary RAG retrieves evidence and blends it. That is unsafe when one
> document is stale, an exception has a narrower scope, or two official sources
> disagree. TruthGuard makes the disagreement visible, explains source trust,
> and abstains when there is no defensible winner.

## Demo 1 — supersession

Question: `What is the hospitalization waiting period for the Standard plan?`

Show the old 30-day policy, the newer 45-day amendment, conflict type T1, the
supersession graph, and the resolved answer.

Say:

> TruthGuard found the old and new positions, followed the amendment
> relationship, and explained why the newer source wins.

## Demo 2 — scope conflict

Question: `Is the co-payment different for a member aged 60 or above?`

Show the 10% standard rule, the 20% senior-member rule, T2 classification, and
the conditional answer.

Say:

> These values are not necessarily contradictory. The conflict is a population
> scope difference, so TruthGuard answers conditionally.

## Demo 3 — exception handling

Question: `Is prior authorization required for every hospital admission?`

Show the planned-admission requirement, emergency exception, T5
classification, and the 24-hour notification condition.

Say:

> The exception is part of the answer. A system that only retrieves the general
> rule may incorrectly say authorization is always required.

## Demo 4 — calibrated abstention

Question: `What is the annual hospitalization limit for the Aurelia Standard plan?`

Show the two same-authority circulars, their conflicting values, T6, and the
abstained answer.

Say:

> The evidence does not justify a winner. Abstention is the correct safety
> behavior, not a failure to answer.

## Demo 5 — not in corpus

Question: `Does Aurelia cover hearing-aid batteries after a routine replacement?`

Show the `not_in_corpus` status and the absence of an invented policy.

Say:

> TruthGuard distinguishes “the corpus disagrees” from “the corpus does not
> contain the answer.”

## Closing statement

> The key result is auditable uncertainty. TruthGuard shows the claims, exact
> evidence, competing documents, trust factors, and final decision. Its
> benchmark reports answer accuracy together with conflict F1, provenance,
> false-conflict rate, and abstention recall.

## Backup commands

```bash
TRUTHGUARD_OFFLINE=true make demo
```

The generated file is `reports/demo_output.md`.
