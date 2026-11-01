# nDCG Evaluation

## Metric

Normalized Discounted Cumulative Gain (nDCG) evaluates ranking quality using graded relevance judgments.

The benchmark uses:

- 2 = Relevant
- 1 = Partially Relevant
- 0 = Not Relevant

nDCG considers both the relevance of each retrieved scheme and its position in the ranking.

## Formula

DCG@k = Σ ((2^rel_i - 1) / log2(i + 1))

nDCG@k = DCG@k / IDCG@k

where IDCG represents the ideal ranking obtained by sorting the relevance scores in descending order.

## Evaluation

Both nDCG@5 and nDCG@10 are calculated using BM25 retrieval results and the manually created graded relevance judgments.

Queries with at least one judged relevant scheme (relevance_score >= 1) are included in the evaluation.

## Interpretation

Higher nDCG indicates that more relevant schemes are ranked closer to the top and that highly relevant schemes receive greater gain than partially relevant schemes.