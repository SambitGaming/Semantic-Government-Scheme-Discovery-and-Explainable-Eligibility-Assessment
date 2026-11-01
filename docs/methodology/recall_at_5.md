# Recall@5

## Metric

Recall@5 measures the proportion of all relevant schemes for a query that are retrieved within the Top 5 BM25 results.

Formula:

Recall@5 =
Relevant schemes retrieved in Top 5
-----------------------------------
Total relevant schemes for the query

## Relevance Threshold

The benchmark uses graded relevance:

- relevance_score = 2: Relevant
- relevance_score = 1: Partially Relevant
- relevance_score = 0: Not Relevant

For the primary Recall@5 evaluation:

relevance_score >= 1

Therefore, both Relevant and Partially Relevant schemes are considered relevant.

## Evaluation Procedure

For each benchmark query, all schemes with relevance_score >= 1 are treated as relevant.

The BM25 Top-5 results are then compared against these relevant schemes using query_id and scheme_id.

Recall@5 is calculated for each query and the mean Recall@5 is reported across all evaluated queries.