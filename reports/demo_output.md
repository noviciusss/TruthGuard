# TruthGuard Judge Demo

This report was generated offline from the committed synthetic corpus. It demonstrates supersession, scope, numeric, exception, abstention, and not-in-corpus behavior without provider calls.

## T1 supersession

**Question:** What is the hospitalization waiting period for the Standard plan?

**Status:** `resolved`

### Answer

Resolved using the highest-trust current position: The non-accidental hospitalization waiting period is 45 days. (AMD-2025-03)

### Conflicts

- `T1` `t1-waiting_period` — AMD-2025-03; Two documents state waiting_period: 45 (unspecified) versus 30 (unspecified); type evidence verified.

### Claims

- `supported` ## Operational rules - **hospitalization waiting period** (standard plan, non-accidental hospitalization): 30 days. (evidence: `FAQ-2024-01:c003, FAQ-2024-01:c002, AMD-2025-03:c002, …`)
- `supported` - **co-payment** (plan and age dependent): 10% for standard plan members. (evidence: `FAQ-2024-01:c003, AMD-2025-03:c003, FAQ-2024-01:c004, …`)
- `supported` - **claim submission deadline** (reimbursement claims): 30 days after discharge. (evidence: `POL-2024-V1:c004`)
- `supported` - **pre-existing condition lookback** (conditions diagnosed or treated before policy start): 36 months. (evidence: `POL-2024-V1:c004`)
- `supported` - **pre-authorization** (planned and emergency admissions): All planned admissions require pre-authorization. (evidence: `POL-2024-V1:c004`)
- `supported` ## Answer The Standard plan has a 30-day waiting period for non-accidental hospitalization. (evidence: `FAQ-2024-01:c003, FAQ-2024-01:c002, AMD-2025-03:c002, …`)
- `supported` ## Operational rules - **hospitalization waiting period** (standard plan, non-accidental hospitalization): 45 days. (evidence: `FAQ-2024-01:c003, FAQ-2024-01:c002, AMD-2025-03:c002, …`)
- `supported` ## Renewals The Standard plan renewal reinstatement grace period is 14 days after the renewal due date. (evidence: `FAQ-2024-01:c003, AMD-2025-03:c002, AMD-2025-03:c003, …`)

### Citations

`AMD-2025-03:c002`, `AMD-2025-03:c003`, `CIR-2026-T6-RENEW-A:c002`, `CIR-2026-T6-RENEW-B:c002`, `FAQ-2024-01:c002`, `FAQ-2024-01:c003`, `FAQ-2024-01:c004`, `FAQ-2025-06:c002`, `POL-2024-V1:c002`, `POL-2024-V1:c004`

---

## T2 scope

**Question:** Is the co-payment different for a member aged 60 or above?

**Status:** `conditional`

### Answer

Conditional answer: The positions apply under different conditions: - **co-payment** (plan and age dependent): 10% for standard plan members; 20% for members aged 60 and above. (CIR-2024-02) - **co-payment** (plan and age dependent): 10% for standard plan members; 20% for members aged 60 and above. (FAQ-2025-01)

### Conflicts

- `T2` `t2-copay` — no single winner; Two documents state copay: 10 (standard) versus 20 (senior); type evidence verified.

### Claims

- `supported` ## Operational rules - **co-payment** (plan and age dependent): 10% for standard plan members; 20% for members aged 60 and above. (evidence: `CIR-2024-02:c003, FAQ-2025-01:c003, FAQ-2025-01:c004`)
- `supported` ## Operational rules - **room rent sub-limit** (plan tier): 1% of sum insured per day for standard plan; 2% of sum insured per day for premium plan. (evidence: `CIR-2024-02:c003, FAQ-2025-01:c003, FAQ-2025-01:c004`)
- `supported` - **co-payment** (plan and age dependent): 10% for standard plan members; 20% for members aged 60 and above. (evidence: `CIR-2024-02:c003, FAQ-2025-01:c003, FAQ-2025-01:c004`)
- `supported` ## Co-payment The Standard plan co-payment rate is 15%. (evidence: `CIR-2024-02:c003, FAQ-2025-01:c003, FAQ-2025-01:c004`)
- `supported` ## Co-payment The Standard plan co-payment rate is 25%. (evidence: `CIR-2024-02:c003, FAQ-2025-01:c003, FAQ-2025-01:c004`)

### Citations

`AMD-2025-05:c002`, `CIR-2024-02:c002`, `CIR-2024-02:c003`, `CIR-2026-T6-COPAY-A:c001`, `CIR-2026-T6-COPAY-A:c002`, `CIR-2026-T6-COPAY-B:c002`, `FAQ-2025-01:c003`, `FAQ-2025-01:c004`

---

## T3 numeric change

**Question:** When does the claim submission window close after discharge?

**Status:** `resolved`

### Answer

Resolved using the highest-trust current position: - **claim submission deadline** (reimbursement claims): 60 days after discharge. (AMD-2025-04)

### Conflicts

- `T3` `t3-claim_deadline` — AMD-2025-04; Two documents state claim_deadline: 60 (unspecified) versus 30 (unspecified); type evidence verified.

### Claims

- `supported` ## Operational rules - **hospitalization waiting period** (standard plan, non-accidental hospitalization): 30 days. (evidence: `AMD-2025-04:c003, MAN-2025-CLAIMS:c003, MAN-2024-CLAIMS:c004`)
- `unsupported` - **co-payment** (plan and age dependent): 10% for standard plan members. (evidence: `none`)
- `supported` - **claim submission deadline** (reimbursement claims): 30 days after discharge. (evidence: `AMD-2025-04:c003, MAN-2025-CLAIMS:c003, AMD-2025-04:c002, …`)
- `unsupported` - **pre-existing condition lookback** (conditions diagnosed or treated before policy start): 36 months. (evidence: `none`)
- `unsupported` - **pre-authorization** (planned and emergency admissions): All planned admissions require pre-authorization. (evidence: `none`)
- `supported` ## Operational rules - **claim submission deadline** (reimbursement claims): 60 days after discharge. (evidence: `AMD-2025-04:c003, MAN-2025-CLAIMS:c003, AMD-2025-04:c002, …`)
- `supported` ## Operational rules - **claim submission deadline** (reimbursement claims): 60 days after discharge. (evidence: `AMD-2025-04:c003, MAN-2025-CLAIMS:c003, AMD-2025-04:c002, …`)
- `supported` ## Operational rules - **claim submission deadline** (reimbursement claims): 30 days after discharge. (evidence: `AMD-2025-04:c003, MAN-2025-CLAIMS:c003, AMD-2025-04:c002, …`)
- `supported` - **excluded cosmetic treatment** (treatment primarily for cosmetic enhancement): Cosmetic treatment is excluded unless medically necessary after an accident. (evidence: `MAN-2024-CLAIMS:c004`)

### Citations

`AMD-2025-04:c002`, `AMD-2025-04:c003`, `CIR-2026-T6-CLAIM-A:c002`, `CIR-2026-T6-CLAIM-A:c003`, `CIR-2026-T6-CLAIM-B:c002`, `CIR-2026-T6-CLAIM-B:c003`, `MAN-2024-CLAIMS:c004`, `MAN-2025-CLAIMS:c003`, `POL-2024-V1:c002`, `POL-2024-V1:c004`

---

## T5 exception

**Question:** Can an emergency admission proceed without prior approval?

**Status:** `conditional`

### Answer

Conditional answer: The positions apply under different conditions: Emergency admissions can proceed without prior approval, followed by notification within 24 hours. (NOTICE-2025-02) - **pre-authorization** (planned and emergency admissions): All planned admissions require pre-authorization. (POL-2025-V2)

### Conflicts

- `T5` `t5-preauthorization` — no single winner; Two documents state preauthorization: not-required-with-notification (emergency) versus required (planned); type evidence verified.

### Claims

- `unsupported` ## Operational rules - **hospitalization waiting period** (standard plan, non-accidental hospitalization): 45 days. (evidence: `none`)
- `unsupported` - **co-payment** (plan and age dependent): 10% for standard plan members. (evidence: `none`)
- `unsupported` - **claim submission deadline** (reimbursement claims): 60 days after discharge. (evidence: `none`)
- `unsupported` - **pre-existing condition lookback** (conditions diagnosed or treated before policy start): 48 months. (evidence: `none`)
- `supported` - **pre-authorization** (planned and emergency admissions): All planned admissions require pre-authorization. (evidence: `NOTICE-2025-02:c002, CIR-2025-06:c002`)
- `supported` ## Emergency care Emergency admissions can proceed without prior approval, followed by notification within 24 hours. (evidence: `NOTICE-2025-02:c002, CIR-2025-06:c002`)
- `supported` ## Emergency exception Emergency admissions may use cashless treatment without prior approval if Aurelia is notified within 24 hours. (evidence: `NOTICE-2025-02:c002, CIR-2025-06:c002, CIR-2025-06:c001`)
- `supported` ## Operational rules - **pre-authorization** (planned and emergency admissions): Emergency admissions may use cashless treatment without prior approval, with notification within 24 hours. (evidence: `NOTICE-2025-02:c002, CIR-2025-06:c002`)
- `supported` - **network hospital cashless eligibility** (planned treatment at an Aurelia network hospital): Cashless treatment is available when the hospital is in the active Aurelia network and approval is obtained. (evidence: `CIR-2025-06:c002`)

### Citations

`AMD-2025-09:c002`, `CIR-2025-06:c001`, `CIR-2025-06:c002`, `CIR-2025-06:c003`, `CIR-2026-T6-PREAUTH-B:c002`, `MAN-2025-CASHLESS:c003`, `NOTICE-2025-02:c002`, `NOTICE-2025-02:c003`, `POL-2025-V2:c000`, `POL-2025-V2:c004`

---

## T6 abstention

**Question:** For a Standard inpatient room, the evidence gives two different caps effective on the same date. Is either cap authoritative?

**Status:** `abstained`

### Answer

I cannot safely resolve this conflict: The sources conflict and have no reliable tie-breaker.

### Conflicts

- `T6` `t6-t6_room_rent_cap` — no single winner; Two documents state t6_room_rent_cap: 1 (standard) versus 2 (standard); type evidence verified.

### Claims

- `supported` ## Room rent The Standard plan inpatient room rent cap is 1% of sum insured per day. (evidence: `CIR-2026-T6-ROOM-A:c002, CIR-2026-T6-ROOM-B:c002, CIR-2026-T6-ROOM-A:c003, …`)
- `supported` ## Room rent The Standard plan inpatient room rent cap is 2% of sum insured per day. (evidence: `CIR-2026-T6-ROOM-A:c002, CIR-2026-T6-ROOM-B:c002, CIR-2026-T6-ROOM-A:c003, …`)
- `supported` ## Renewals The Standard plan renewal reinstatement grace period is 14 days after the renewal due date. (evidence: `CIR-2026-T6-ROOM-A:c002, CIR-2026-T6-ROOM-B:c002, CIR-2026-T6-ROOM-A:c003, …`)
- `supported` ## Renewals The Standard plan renewal reinstatement grace period is 21 days after the renewal due date. (evidence: `CIR-2026-T6-ROOM-A:c002, CIR-2026-T6-ROOM-B:c002, CIR-2026-T6-ROOM-A:c003, …`)

### Citations

`CIR-2026-T6-RENEW-A:c002`, `CIR-2026-T6-RENEW-B:c002`, `CIR-2026-T6-ROOM-A:c002`, `CIR-2026-T6-ROOM-A:c003`, `CIR-2026-T6-ROOM-B:c002`, `CIR-2026-T6-ROOM-B:c003`, `NOTICE-2025-11:c002`, `POL-2025-V2:c003`

---

## T7 unknown

**Question:** Does Aurelia cover hearing-aid batteries after a routine replacement?

**Status:** `not_in_corpus`

### Answer

This question is not answerable from the available corpus.

### Conflicts

- No conflict was retained by the critic.

### Claims

- `unsupported` --- Doc ID: POL-2024-V1 Title: Aurelia Health Standard Policy Wording v1 Type: policy Version: 1.0 Effective: Issued: 2023-12-15 Supersedes: Amends: --- ## Renewals A renewal may be completed within 30 days after the du… (evidence: `none`)
- `unsupported` ## Section 8.2 A reimbursement claim must be submitted within 60 days after discharge. (evidence: `none`)
- `unsupported` ## Exclusions Cosmetic treatment is excluded unless medically necessary after an accident. (evidence: `none`)

### Citations

`AMD-2025-04:c002`, `AMD-2025-04:c003`, `CIR-2024-01:c002`, `CIR-2026-T6-ROOM-A:c000`, `CIR-2026-T6-ROOM-A:c003`, `CIR-2026-T6-ROOM-B:c003`, `MAN-2024-CLAIMS:c003`, `MAN-2025-CLAIMS:c003`, `POL-2024-V1:c000`, `POL-2024-V1:c001`

---
