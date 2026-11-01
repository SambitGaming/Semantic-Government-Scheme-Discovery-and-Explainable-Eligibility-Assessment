# MPNet Retrieval Methodology

## 1. Model

The retrieval system uses `sentence-transformers/all-mpnet-base-v2`.

## 2. Embedding dimension

Each scheme document and benchmark query is represented by a 768-dimensional embedding.

## 3. Corpus

The system uses the same frozen scheme corpus stored in `data/processed/bm25_corpus.csv`, ensuring consistency with BM25 and MiniLM.

## 4. Query dataset

The same benchmark queries are used for all three retrieval models. Query wording is not changed to improve results.

## 5. Similarity

Embeddings are normalized, and cosine similarity is calculated using the dot product.

## 6. Retrieval depth

The system retrieves up to 10 schemes per query, ordered by descending similarity score.

## 7. Relevance judgments

The independent relevance judgments use graded labels: 2 = Relevant, 1 = Partially Relevant, and 0 = Not Relevant. Unjudged scheme-query pairs are not automatically classified as irrelevant.

## 8. Evaluation metrics

The evaluation includes Precision@5, Recall@5, Precision@10, Recall@10, Mean Reciprocal Rank (MRR), nDCG@5, and nDCG@10.

For binary precision and recall, relevance is defined using the same threshold as the BM25 and MiniLM evaluations. Graded relevance is retained for nDCG.

## 9. Error analysis

The analysis identifies potentially incorrect top-ranked schemes, relevant schemes ranked lower, and unjudged results requiring review.

## 10. Reproducibility and limitations

The corpus, queries, relevance judgments, relevance threshold, and retrieval depth are kept consistent across the three models. Evaluation results are interpreted in light of judgment coverage and the benchmark's limitations.
