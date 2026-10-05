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
| FR-5 | A gap is **material** when its severity is high. Only the items listed in section 4.1 are high severity. |
| FR-6 | The system shall return exactly one verdict: In Appetite, Refer to Underwriter, or Decline. |
| FR-7 | Every verdict shall carry reasons, and each reason shall name the rule it applies. |
| FR-8 | The appetite ruleset shall be displayed to the user alongside the result. |
| FR-9 | The system shall draft a broker email consistent with the verdict (section 6.2). |
| FR-10 | The system shall not send the email or record a decision; a person reviews every output. |

### 4.1 Material information

A gap is high severity, and so triggers rule R4, only when one of these is true:

- the business class or operations are unclear
- time in business is not stated
- loss history is not provided, or the submission contradicts itself about losses
- requested coverages are not stated, or GL is requested and GL limits are not stated
- property coverage is requested and property values are not stated
- restaurants: whether alcohol is served is not stated
- habitational risks: the number of units is not stated

Naming these is what makes "material information missing" testable. Everything else, such as the prior carrier's name or building construction, is medium or low.

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
    "rules": ["D1"],
    "reasons": ["string"]
  },
  "draftEmail": { "subject": "string", "body": "string" }
}
```

`appetite.rules` lists the decision-table IDs that apply. It was added for the evaluation: a rule ID can be scored exactly, where a sentence cannot. The hosted demo page predates it and does not display it.

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

Definitions used by the rules:

- "Last three years" means the three years before the effective date.
- A loss amount is its total incurred: paid plus reserve.
- Property total insured value is building plus business personal property plus business income or rental income.
- Thresholds are strict: a loss of exactly $100,000, a TIV of exactly $10M and exactly two years in business do not trigger D4, R1 or R2.

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

## 8. Evaluation

The hosted demo replays pre-generated analyses, so accuracy is measured separately. A golden set of 30 submissions is run through a live model in GitHub Actions, scored automatically, and published at [eval.html](https://siddharthwaghmare.github.io/submissioniq/eval.html) once a run completes. No run has completed yet.

| Part | Location |
|---|---|
| Test cases and expected answers | `eval/golden_set.json`, built from `eval/build_golden.py` |
| Model prompt, including the rules | `eval/prompt.md` |
| Scoring code | `eval/run_eval.py` |
| Workflow | `.github/workflows/eval.yml` |
| Results and run history | `eval/results/` |

### 8.1 Golden set

Thirty cases: 10 Decline, 12 Refer to Underwriter, 8 In Appetite. Every rule has at least one case. Each case states the expected verdict, the rules that must be cited, the rules that must not be cited, and selected fields to check.

The set includes these deliberate traps:

| Case | Trap |
|---|---|
| G10 | Two losses, one open: D2 must win over R3 |
| G11 | Four losses and missing limits: Decline must win over Refer |
| G12 | A single loss of exactly $100,000: D4 must not fire |
| G15 | Property values of exactly $10M: R1 must not fire |
| G17 | Exactly two years in business: R2 must not fire |
| G23 | A 310-unit self-storage facility: must not be read as habitational |
| G25 | Exactly 50 apartment units: still a target class |
| G26 | The email says "no claims" and the pasted loss run shows one |
| G30 | Three losses, only one inside the three-year window |

### 8.2 Assumptions in the expected answers

- A submission that contradicts itself on losses (G26) is referred under R4.
- Habitational over 50 units (G24) is referred under R5, not declined.
- D2 and D4 apply to any claim shown on the loss runs, with no lookback limit.

### 8.3 Measures

| Measure | Definition | Target |
|---|---|---|
| Verdict accuracy | Cases with the expected verdict | 100% |
| Unsafe verdicts | Cases returned In Appetite when expected Refer or Decline | 0 |
| Field accuracy | Checked fields that match the submission | 95% or higher |
| Invented values | Fields given a value the submission does not state | 0 |
| Rule accuracy | Cases citing every required rule and no forbidden rule | 100% |
| Reason traceability | Cases whose cited rule IDs all exist in the decision table | 100% |
| Contract validity | Responses that parse against the output contract | 100% |
| Decline emails clean | Decline emails that ask the broker for nothing | 100% |

Unsafe verdicts matter most. Referring a clean risk costs an underwriter a few minutes; passing a risk that should have been declined costs a loss.

### 8.4 Limits of this evaluation

- Thirty cases is small. A passing run shows the rules are applied correctly on these cases, not on every submission.
- Field checks cover selected fields per case, not all twelve.
- The cases were written alongside the prompt, so they favor it. Real broker submissions would be a harder test.

## 9. Controls

- **Human in the loop:** no output is sent or recorded without review (FR-10).
- **Auditability:** the ruleset is visible, and every reason names its rule (FR-7, FR-8).
- **Rule ownership:** the ruleset is configuration owned by underwriting, not logic hidden in a prompt.
- **Data:** a production build would need a privacy review, since submissions carry business and personal information.

## 10. Known limitations

- The hosted page replays pre-generated analyses and does not call a model live; the live model runs in the evaluation only.
- Input is pasted text only; real submissions arrive as PDFs, spreadsheets and scans.
- The ruleset is illustrative and far smaller than a carrier's underwriting guide.
- Loss counting assumes the loss run is complete and current.
