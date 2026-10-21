# TruthGuard five-minute pitch

## 0:00–0:30 — Problem

“Policy assistants usually produce one fluent answer even when their sources
disagree. TruthGuard makes the disagreement visible, preserves the competing
passages, and chooses among resolution, conditional answer, abstention, or
missing evidence.”

Say up front: this is a fictional Aurelia Health corpus and a deterministic
offline demonstration. The pitch numbers are labeled in
[`reports/PITCH_NUMBERS.md`](../reports/PITCH_NUMBERS.md).

## 0:30–1:00 — Architecture

Show the flow: retrieval → passage-grounded draft → claim/conflict critic →
trust factors and supersession graph → resolver. Emphasize that the measured
headline path is deterministic/offline; optional LLM criticism is a separate,
quota-sensitive path and has no completed v2 live result.

## 1:00–3:35 — Live demo order

Use the Streamlit app's v2 example questions. For each question, show the
status, claims, citations, conflict positions, and trace.

### 1. T1 — supersession

Question: “What is the hospitalization waiting period for the Standard plan?”

Show the older 30-day policy and the 45-day amendment. TruthGuard identifies a
temporal conflict and resolves to the governing amendment.

### 2. T2 — scope

Question: “Is the co-payment different for a member aged 60 or above?”

Show 10% for Standard and 20% for senior members. The answer is conditional,
not a forced single percentage.

### 3. T3 — numeric/version conflict

Question: “When does the claim submission window close after discharge?”

Show the historical 30-day rule and the current 60-day amendment. Explain that
T3 is common in TEST: 36 of 146 rows, or 24.7%, so both micro and macro metrics
are reported.

### 4. T5 — exception

Question: “Can an emergency admission proceed without prior approval?”

Show the planned-admission approval rule and the emergency notification
exception. The conditions remain visible in the conditional answer.

### 5. T6 — genuine abstention

Question: “For a Standard inpatient room, the evidence gives two different caps
effective on the same date. Is either cap authoritative?”

Show the two new circulars: 1% and 2%, equal authority and effective date, with
no third document or later amendment resolving the fact. TruthGuard abstains.
This is a genuine whole-corpus tie, not the old annual-limit example.

### 6. T7 — missing evidence

Question: “Does Aurelia cover hearing-aid batteries after a routine replacement?”

Show `not_in_corpus`. Explain that missing evidence is different from a
contradiction.

## 3:35–4:15 — Compare-mode moment

Open Compare mode on the T6 room-rent question. In the measured deterministic
offline smoke, B0 and B1 both produced a value-containing passage blend with
`no_conflict` and no retained conflict, while TruthGuard abstained with one T6
conflict. This is an observed UI example, not a live B0/B1 benchmark result.

If time permits, show the T3 question as well: the passage-only baseline can
repeat a value, while TruthGuard exposes the governing document and conflict
type. Do not call this production superiority; the formal no-critic TEST
ablation had answer proxy 0.8082 but conflict F1 0.0000.

## 4:15–5:00 — Limitations and close

“The corpus is synthetic: 47 fictional documents and 20 factsheet keys. The
benchmark is templated by the same team, with 190 main questions and 22 wild
questions; human review agreement is pending. TEST is T3-heavy, so we report
micro and macro metrics. Wild conflict F1 is 0.56 versus TEST 0.8835 on the
deterministic path. Provenance is document-level, not semantic. Seven corrupted
versions remain unknown with zero confidence. User-facing as-of-date queries are
not supported. The v2 live critic and baseline runs completed zero questions
because no provider credential was available, so there is no live v2 claim.”

Close with: “The contribution is inspectable disagreement handling, not a claim
of production accuracy.”
