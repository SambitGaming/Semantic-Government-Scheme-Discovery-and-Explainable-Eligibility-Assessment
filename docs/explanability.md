# Explainability and Traceability

## Objective

The eligibility system provides human-readable explanations
for every eligibility decision.

The system does not only return Eligible or Not Eligible.
It also identifies the individual rules that passed or failed.

## Decision Process

The decision process is:

User Profile
    ↓
Scheme Selection
    ↓
Retrieve Rules
    ↓
Evaluate Individual Rules
    ↓
Aggregate Results
    ↓
Eligibility Decision
    ↓
Generate Explanation

## Rule-Level Information

For every evaluated rule, the system records:

- Rule ID
- Scheme ID
- User value
- Required value
- Operator
- Pass/Fail result
- Explanation
- Rule version
- Official source URL

## Explainability

If the applicant is eligible, the system reports that
all mandatory rules were satisfied.

If the applicant is not eligible, the system identifies
the specific rule or rules that failed.

## Traceability

Every rule contains a rule ID, version and source URL.

Therefore, an eligibility decision can be traced through:

Final Decision
    ↓
Rule Result
    ↓
Rule ID
    ↓
Scheme ID
    ↓
Rule Version
    ↓
Official Source

## Multiple Failed Rules

The system supports multiple failed rules.

For example:

Rule R001 → FAIL
Rule R004 → FAIL
Rule R006 → FAIL

The explanation output reports all failed rules rather
than stopping after the first failure.

## Versioning

Each rule contains a version number.

This allows the system to identify the rule version used
when producing an eligibility decision.

## Output

The system generates:

`results/eligibility/explainability_results.csv`

This file contains rule-level explanations for the
Gold Profile evaluation dataset.

## Conclusion

The explainability layer makes the eligibility engine
more transparent and traceable by connecting each
eligibility decision to the individual rules used to
produce that decision.