# SubmissionIQ — Business Analysis Specification

Author: Siddharth Waghmare · Status: portfolio demonstration · Data: fictional

This document is the BA deliverable behind SubmissionIQ: the problem, the requirements, the output contract, the appetite rules as a decision table, the acceptance criteria, and the plan for evaluating a live model against them.

## 1. Problem and scope

Commercial submission intake is manual. An underwriting assistant reads a broker email and its attachments, re-keys the data, checks it against appetite, and replies to the broker. It is slow, and two people can reach different answers on the same risk.

**In scope:** first-pass triage of a small-commercial submission received as free text: extraction, gap detection, appetite verdict, and a drafted broker reply.

**Out of scope:** pricing and rating, binding, reading PDF or scanned attachments, writing to a policy administration system, and any final underwriting decision.

## 2. Process: current and future state

| Step | Current state | Future state with SubmissionIQ |
|---|---|---|
| Read submission | Assistant reads email, ACORD forms, loss runs | Model reads the full text |
| Capture data | Re-keyed by hand | Extracted into a fixed set of fields |
| Check completeness | From memory or a checklist | Each gap listed with a severity |
| Check appetite | Judgment, varies by person | Verdict from an explicit ruleset, with reasons |
| Reply to broker | Written from scratch | Draft produced; a person reviews and sends |
| Decision authority | Underwriter | Underwriter (unchanged) |

## 3. Users

| User | Need |
|---|---|
| Underwriting assistant | Stop re-keying; know what to ask the broker for |
| Underwriter | See a complete, pre-triaged risk with the reasons for its verdict |
| Underwriting manager | Appetite applied the same way across the team; rules that can be audited |
| Broker | A fast, specific answer or information request |

## 4. Functional requirements

| ID | Requirement |
|---|---|
| FR-1 | The system shall accept a submission as free text. |
| FR-2 | The system shall extract the twelve fields in the output contract (section 5). |
| FR-3 | Where a field is not stated in the submission, the system shall return "Not specified" and shall not infer a value. |
| FR-4 | The system shall list missing or incomplete information, each with a severity of high, medium or low. |
| FR-5 | A gap is **material** when its severity is high: the appetite decision or the ability to quote depends on it. |
| FR-6 | The system shall return exactly one verdict: In Appetite, Refer to Underwriter, or Decline. |
| FR-7 | Every verdict shall carry reasons, and each reason shall name the rule it applies. |
| FR-8 | The appetite ruleset shall be displayed to the user alongside the result. |
| FR-9 | The system shall draft a broker email consistent with the verdict (section 6.2). |
| FR-10 | The system shall not send the email or record a decision; a person reviews every output. |

## 5. Output contract

The model returns one JSON object in this shape. A fixed shape is what makes the output renderable and testable.

```json
{
  "extracted": {
    "namedInsured": "string",
    "businessClass": "string",
    "location": "string",
    "coverages": "string",
    "glLimits": "string",
    "propertyValues": "string",
    "annualRevenue": "string",
    "employees": "string",
    "yearsInBusiness": "string",
    "effectiveDate": "string",
    "priorCarrier": "string",
    "lossSummary": "string"
  },
  "missing": [
    { "field": "string", "note": "string", "severity": "high | medium | low" }
  ],
  "appetite": {
    "verdict": "In Appetite | Refer to Underwriter | Decline",
    "reasons": ["string"]
  },
  "draftEmail": { "subject": "string", "body": "string" }
}
```

## 6. Appetite rules

### 6.1 Decision table

Rules are evaluated in this order. The first group that matches sets the verdict: **Decline overrides Refer, and Refer overrides In Appetite.**

| # | Condition | Verdict |
|---|---|---|
| D1 | Class is cannabis, adult entertainment or heavy manufacturing | Decline |
| D2 | Any open or litigated claim | Decline |
| D3 | Three or more losses in the last three years | Decline |
| D4 | Any single loss over $100,000 | Decline |
| R1 | Property total insured value over $10M | Refer to Underwriter |
| R2 | Less than two years in business | Refer to Underwriter |
| R3 | Exactly two losses in the last three years | Refer to Underwriter |
| R4 | Any material (high-severity) information missing | Refer to Underwriter |
| A1 | Target class (restaurant, office, light retail, artisan contractor, habitational up to 50 units) and no D or R rule matched | In Appetite |
| R5 | Class is not a target class and not a declined class | Refer to Underwriter |

R5 is a rule this specification adds. The ruleset on the page does not say what happens to a class that is neither targeted nor declined; referring it is the safe default.

### 6.2 Email behavior by verdict

| Verdict | The draft email shall |
|---|---|
| In Appetite | Confirm appetite and next step; request only non-blocking rating details |
| Refer to Underwriter | State why it is referred; request every high and medium gap |
| Decline | State the rule(s) met; request no information; say what would change the answer |

## 7. Acceptance criteria

**AC-1 Extraction**
Given a submission that states the named insured, class and effective date
When the analysis runs
Then each of those fields matches the submission exactly.

**AC-2 No invented values**
Given a submission that does not state GL limits
When the analysis runs
Then `glLimits` is "Not specified" and a gap is raised for it.

**AC-3 Refer on material gap**
Given a target-class risk with no decline trigger and one high-severity gap
When the analysis runs
Then the verdict is "Refer to Underwriter" and a reason cites the missing information.

**AC-4 Decline precedence**
Given a target-class risk with three losses in three years and also missing information
When the analysis runs
Then the verdict is "Decline", not "Refer to Underwriter".

**AC-5 Open claim**
Given a risk with one open claim under $100,000
When the analysis runs
Then the verdict is "Decline" and the reason cites the open-claim rule, not the single-loss rule.

**AC-6 Clean risk**
Given a target-class risk, two or more years in business, no losses and only low-severity gaps
When the analysis runs
Then the verdict is "In Appetite".

**AC-7 Decline email asks for nothing**
Given a verdict of "Decline"
When the email is drafted
Then it contains no information request.

**AC-8 Reasons trace to rules**
Given any verdict
When the reasons are listed
Then each reason maps to a row of the decision table.

## 8. Evaluation plan

The hosted demo replays pre-generated analyses, so it has no accuracy figures to report. This section defines how a live-model build would be measured.

### 8.1 Golden set

The three sample submissions are the first golden cases. Each has an expected verdict and expected rule hits.

| Case | Expected verdict | Rules that must be cited | Rules that must not be cited |
|---|---|---|---|
| The Copper Skillet (restaurant) | Refer to Underwriter | R4 | Any D rule |
| Summit Air Mechanical (HVAC) | Decline | D2, D3 | D4 |
| Larkfield Analytics (office) | In Appetite | A1 | Any D or R rule |

A usable golden set needs more than three cases. The target is 30, with at least one case per rule and the boundary cases below.

### 8.2 Boundary cases to add

- Exactly two years in business (R2 must not fire)
- A single loss of exactly $100,000 (D4 must not fire)
- Property TIV of exactly $10M (R1 must not fire)
- Two losses, one of them open (D2 must win over R3)
- A class outside both lists, for example a daycare (R5)
- A submission that contradicts itself, for example "no losses" in the email and a claim in the loss run

### 8.3 Measures

| Measure | Definition | Target |
|---|---|---|
| Field accuracy | Extracted fields matching the expected value, over all fields | 95% or higher |
| Invented-value rate | Fields given a value the submission does not contain | 0 |
| Verdict accuracy | Cases with the expected verdict | 100% on the golden set |
| Unsafe-verdict rate | Cases returned In Appetite when expected Refer or Decline | 0 |
| Reason traceability | Reasons that map to a decision-table row | 100% |
| Contract validity | Responses that parse against the output contract | 100% |

Unsafe-verdict rate matters most. Referring a clean risk costs an underwriter a few minutes; passing a risk that should have been declined costs a loss.

## 9. Controls

- **Human in the loop:** no output is sent or recorded without review (FR-10).
- **Auditability:** the ruleset is visible, and every reason names its rule (FR-7, FR-8).
- **Rule ownership:** the ruleset is configuration owned by underwriting, not logic hidden in a prompt.
- **Data:** a production build would need a privacy review, since submissions carry business and personal information.

## 10. Known limitations

- The hosted page replays pre-generated analyses and does not call a model live.
- Input is pasted text only; real submissions arrive as PDFs, spreadsheets and scans.
- The ruleset is illustrative and far smaller than a carrier's underwriting guide.
- Loss counting assumes the loss run is complete and current.
