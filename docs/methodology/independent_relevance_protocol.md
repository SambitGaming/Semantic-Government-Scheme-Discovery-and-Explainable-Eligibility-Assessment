# Independent Relevance Judgment Protocol

## 1. Purpose

This protocol defines how a second evaluator will independently review a subset of relevance judgments in the government scholarship retrieval benchmark.

The purpose is to improve the reliability and transparency of the relevance labels.

## 2. Scope

The protocol applies to the benchmark queries and scheme-query relevance judgments stored in:

* data/benchmark/queries.csv
* data/benchmark/relevance_judgments.csv

## 3. Independent Review

A second evaluator will independently review a subset of benchmark queries.

For an initial benchmark of 100 queries, approximately 20–30 queries may be selected for independent review.

The selected queries should represent different query categories and difficulty levels.

The second evaluator should not rely on the original evaluator's relevance labels while making independent judgments.

## 4. Judgment Labels

The second evaluator will use the same labels:

| Label              | Score |
| ------------------ | ----: |
| Relevant           |     2 |
| Partially Relevant |     1 |
| Not Relevant       |     0 |

## 5. Judgment Criteria

The evaluator will compare:

* User query requirements
* Scheme eligibility
* Study level
* Target group
* Scheme purpose
* Benefits
* Other relevant conditions

The evaluator will assign a label and provide a short justification.

## 6. Recording Disagreements

Any disagreement between the primary evaluator and second evaluator will be recorded.

The disagreement record should contain:

* Query ID
* Scheme ID
* Primary evaluator label
* Second evaluator label
* Primary justification
* Second justification
* Final resolution
* Reason for resolution

## 7. Resolving Disagreements

Disagreements will be reviewed using the predefined relevance criteria.

If the disagreement cannot be resolved immediately, the case will be marked for discussion.

The final resolution should be documented rather than silently changing a label.

## 8. Reporting

The final report should state:

* Number of queries independently reviewed
* Number of scheme-query judgments reviewed
* Number of disagreements
* How disagreements were resolved
* Any limitations of the review

## 9. Reproducibility

The independent review records will be retained with the benchmark materials.

Changes to relevance judgments will be documented and version-controlled.