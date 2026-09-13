# Benchmark Query Construction Protocol

## 1. Purpose

The benchmark evaluates government scholarship and education scheme retrieval using natural-language citizen queries.

The same fixed benchmark will be used to compare BM25, all-MiniLM-L6-v2, and all-mpnet-base-v2.

The benchmark is intended to evaluate retrieval quality, not official eligibility approval or application acceptance.

## 2. Corpus

The benchmark will be constructed after freezing Government Scholarship Corpus V1.0.

The benchmark will use the same fixed scheme corpus for all retrieval methods.

No scheme will be added or removed during benchmark construction without creating a new corpus version.

The final corpus version and total scheme count will be recorded after corpus validation.

## 3. Query Categories

The benchmark will contain the following query categories:

1. Direct queries
2. Colloquial/natural-language queries
3. Constraint-based queries
4. Underspecified queries
5. Ambiguous queries
6. Hard-negative queries

## 4. Initial Benchmark Size

An initial pilot benchmark of 5 queries will be created to check the corpus and query construction process.

The initial full benchmark target is approximately 100 queries.

The target distribution is:

| Query Type       | Target |
| ---------------- | -----: |
| Direct           |     20 |
| Colloquial       |     20 |
| Constraint-based |     20 |
| Underspecified   |     15 |
| Ambiguous        |     15 |
| Hard negatives   |     10 |
| Total            |    100 |

The benchmark may later be expanded toward 300–500 queries, depending on project timeline and corpus readiness.

## 5. Query Construction Principles

Queries should:

* Represent realistic citizen information needs.
* Use natural language.
* Include different levels of specificity.
* Include single and multiple constraints.
* Include ambiguous and underspecified requests.
* Include difficult cases and hard negatives.
* Avoid systematically favoring any retrieval model.
* Avoid revealing the exact scheme name whenever possible.
* Be based on the frozen corpus.
* Avoid copying official scheme descriptions verbatim.
* Preserve the intended difficulty of each query category.

## 6. Relevance Labels

Each scheme-query pair will receive one of three labels.

### Relevant — Score 2

The scheme directly satisfies the important requirements expressed in the query.

### Partially Relevant — Score 1

The scheme matches some important aspects of the query but does not fully satisfy the stated requirements.

### Not Relevant — Score 0

The scheme does not meaningfully satisfy the user's requirements.

## 7. Relevance Judgment

Relevance will be judged using information contained in the frozen scheme corpus, including:

* Eligibility
* Study level
* Target group
* Scheme purpose
* Benefits
* Other relevant conditions

For constraint-based queries, important stated constraints will be considered when assigning relevance.

The judgment justification will explain why a scheme received its label.

## 8. Independent Judgment

A subset of benchmark judgments will be independently reviewed by a second evaluator.

For an initial benchmark of 100 queries, a subset of approximately 20–30 queries may be independently reviewed.

The exact subset and selection procedure will be recorded before independent review.

Disagreements will be recorded and reviewed using the predefined relevance criteria.

## 9. Query Identifiers

Each query will receive a unique identifier in the format:

Q001, Q002, Q003, etc.

## 10. Reproducibility

The following files will be maintained:

* queries.csv
* relevance_judgments.csv
* query_generation_log.csv

The query text, query type, relevance judgments, justification, and query-generation metadata will be stored in version-controlled files.

## 11. Model Comparison

BM25, all-MiniLM-L6-v2, and all-mpnet-base-v2 will receive the same benchmark queries.

All retrieval methods will be evaluated against the same relevance judgments and the same frozen scheme corpus.

## 12. Benchmark Limitations

The benchmark evaluates retrieval relevance based on the available corpus information.

It does not establish that a citizen is officially eligible for a government scheme.

Final eligibility must be confirmed using authoritative government guidelines and official sources.

The benchmark will be updated only through a documented corpus or benchmark version change.