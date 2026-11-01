# MiniLM Semantic Retrieval Methodology

## 1. Objective

To implement and evaluate semantic retrieval for government scholarship and education schemes.

## 2. Model

sentence-transformers/all-MiniLM-L6-v2

## 3. Dataset

The same frozen scheme corpus used by the BM25 retrieval system.

## 4. Input Fields

Scheme documents are represented using the `bm25_document` field. Benchmark queries are taken from `benchmark_queries.csv`.

## 5. Embedding Generation

MiniLM converts scheme documents and search queries into 384-dimensional numerical embeddings.

## 6. Normalization

Embeddings are normalized before similarity calculation.

## 7. Similarity Measure

Cosine similarity, calculated using the dot product of normalized embeddings.

## 8. Retrieval

Schemes are ranked by similarity score, and the top 10 are saved for each query.

## 9. Benchmark

The same benchmark queries and relevance judgments used for BM25 are used for MiniLM.

## 10. Relevance Labels

* 2: Relevant
* 1: Partially Relevant
* 0: Not Relevant

For binary metrics, relevance scores greater than or equal to 1 are treated as relevant.

## 11. Evaluation Metrics

Precision@5, Recall@5, Precision@10, Recall@10, Mean Reciprocal Rank (MRR), nDCG@5 and nDCG@10.

## 12. Error Analysis

Inspect potentially irrelevant results, relevant schemes ranked below position 5, ambiguous queries and hard-negative cases.

## 13. Reproducibility

The model checkpoint, corpus, benchmark, relevance judgments and evaluation protocol are kept consistent for comparisons with BM25 and MPNet.

## 14. Limitations

Semantic similarity does not guarantee eligibility. Retrieved schemes must be checked against their documented eligibility requirements and official sources.
