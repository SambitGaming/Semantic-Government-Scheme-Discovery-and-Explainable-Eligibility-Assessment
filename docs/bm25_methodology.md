# BM25 Retrieval Methodology

## 1. Corpus Size

The BM25 retrieval corpus was created from the processed government scholarship and education scheme dataset.

Each scheme was converted into one searchable document. The corpus size corresponds to the number of schemes available in the processed dataset used for the BM25 experiment.

The corpus was stored in:

```text
data/processed/bm25_corpus.csv
```

Each document contains a unique document ID, scheme ID, scheme name, and the combined searchable text.

The exact corpus size was recorded from the generated BM25 corpus rather than assuming a fixed number of schemes.

---

## 2. Fields Used

The following fields from the scheme dataset were combined to create the BM25 searchable document:

* Scholarship
* Description
* Benefits
* Eligibility
* Category
* Keywords

The combined representation was stored in the `bm25_document` field.

The document structure was:

```text
document_id
scheme_id
scheme_name
bm25_document
```

This allows BM25 to search information describing the scheme, its benefits, eligibility requirements, category, and relevant keywords.

---

## 3. Text Preprocessing

Basic text preprocessing was performed before creating the BM25 corpus.

The preprocessing included:

* Handling missing values
* Converting values to strings
* Removing leading and trailing whitespace
* Combining the selected scheme fields into a single searchable document

Missing values were converted to empty strings so that they did not cause errors during corpus construction.

No aggressive normalization was applied because the BM25 baseline is intended to preserve the original lexical information in the scheme descriptions.

---

## 4. Tokenization

BM25 operates on individual terms/tokens.

The combined `bm25_document` text was tokenized before being passed to the BM25 implementation.

Tokenization allows the retrieval system to compare terms appearing in the user's query with terms occurring in government scheme documents.

The BM25 baseline primarily relies on lexical term matching rather than semantic similarity.

---

## 5. BM25 Implementation

BM25 was used as the initial lexical retrieval baseline for the government scheme discovery system.

BM25 ranks documents according to factors including:

* Query term occurrence
* Term frequency
* Document frequency
* Document length

The BM25 score therefore increases when query terms occur in a scheme document while also accounting for how common those terms are across the corpus.

The BM25 implementation was used to retrieve and rank candidate government schemes for each benchmark query.

---

## 6. Top-K Retrieval

For each benchmark query, BM25 produced ranked scheme results.

The retrieval system generated up to the Top-10 results for evaluation.

The ranking positions were represented as:

```text
Rank 1
Rank 2
Rank 3
...
Rank 10
```

Top-5 and Top-10 results were then used for evaluation.

The following metrics were calculated:

* Precision@5
* Recall@5
* Precision@10
* Recall@10
* MRR
* nDCG@5
* nDCG@10

---

## 7. Benchmark Query Dataset

BM25 was evaluated using the manually constructed benchmark query dataset.

The benchmark contains different query types designed to represent realistic government scholarship discovery requests.

The query categories include:

* Direct
* Colloquial
* Constraint-based
* Underspecified
* Ambiguous

The benchmark was stored in:

```text
data/benchmark/queries.csv
```

Each query contains:

```text
query_id
query_text
query_type
```

The benchmark was designed to test both straightforward scholarship searches and more difficult queries containing limited, ambiguous, or multiple constraints.

---

## 8. Relevance Labels

The benchmark uses graded relevance judgments.

The relevance scale is:

```text
2 = Relevant
1 = Partially Relevant
0 = Not Relevant
```

The judgments are stored in:

```text
data/benchmark/relevance_judgments.csv
```

For binary retrieval metrics such as Precision and Recall, the evaluation protocol uses:

```text
relevance_score >= 1
```

as the definition of a relevant result.

Therefore:

```text
2 → Relevant
1 → Relevant for Precision/Recall
0 → Not Relevant
```

For nDCG, the original graded relevance values are retained so that highly relevant schemes receive greater gain than partially relevant schemes.

---

## 9. Evaluation Metrics

The BM25 system was evaluated using multiple retrieval metrics.

### Precision@5

Measures the proportion of the Top-5 retrieved schemes that are relevant.

```text
Precision@5 =
Relevant results in Top-5
-------------------------
5
```

### Recall@5

Measures how many of the relevant schemes were retrieved within the Top-5 results.

```text
Recall@5 =
Relevant schemes retrieved in Top-5
------------------------------------
All relevant schemes
```

### Precision@10

Measures the proportion of the Top-10 retrieved schemes that are relevant.

### Recall@10

Measures the proportion of all relevant schemes that were retrieved within the Top-10 results.

### MRR

Mean Reciprocal Rank measures how highly the first relevant result appears.

```text
RR = 1 / rank of first relevant result
```

MRR is the average reciprocal rank across evaluated queries.

### nDCG@5 and nDCG@10

Normalized Discounted Cumulative Gain evaluates ranking quality using the graded relevance labels.

nDCG considers both:

1. The relevance of a retrieved scheme
2. Its position in the ranking

Therefore, a highly relevant scheme appearing near Rank 1 contributes more than the same scheme appearing near Rank 10.

---

## 10. Treatment of Unjudged Documents

A retrieved scheme that does not have a corresponding relevance judgment is treated as having:

```text
relevance_score = 0
```

for the retrieval evaluation.

This prevents missing judgments from being incorrectly treated as relevant.

However, queries with no judged relevant schemes require special handling for metrics such as Recall because the denominator would otherwise be zero.

The evaluation scripts therefore explicitly handle cases where no relevant judgment exists rather than silently assigning an arbitrary recall value.

The evaluation population and relevance threshold are documented alongside the generated metric results.

---

## 11. Error-Analysis Procedure

A qualitative error analysis was performed after calculating the quantitative BM25 metrics.

Four major error categories were examined:

### 11.1 Relevant scheme missed

A scheme judged relevant was not retrieved within the Top-10 results.

This indicates that BM25 failed to retrieve a relevant candidate for the query.

### 11.2 Irrelevant scheme ranked first

An irrelevant scheme received Rank 1.

This can occur when lexical overlap between the query and scheme document is high even though the scheme does not adequately satisfy the user's requirements.

### 11.3 Relevant scheme ranked too low

A relevant scheme was retrieved at a low position such as Rank 9 or Rank 10.

In this case BM25 successfully retrieved the scheme but did not rank it sufficiently high.

### 11.4 Ambiguous or underspecified query

Ambiguous and underspecified queries were examined separately.

These queries may contain insufficient information about the user's actual requirements. BM25 may therefore retrieve schemes based mainly on matching words rather than understanding the underlying intent or eligibility constraints.

The consolidated error analysis was saved to:

```text
results/bm25/bm25_errors.csv
```

The per-query evaluation results were saved to:

```text
results/bm25/bm25_per_query.csv
```

The overall BM25 metrics were saved to:

```text
results/bm25/bm25_metrics.csv
```

---

## Summary

BM25 provides the lexical retrieval baseline for the government scholarship discovery system.

The baseline uses the combined scheme name, description, benefits, eligibility, category, and keyword information to retrieve schemes for benchmark queries.

Its performance is evaluated using both binary retrieval metrics and graded-ranking metrics. The error analysis identifies cases where lexical matching is insufficient, providing a basis for comparison with semantic retrieval approaches such as sentence-transformer-based models.
