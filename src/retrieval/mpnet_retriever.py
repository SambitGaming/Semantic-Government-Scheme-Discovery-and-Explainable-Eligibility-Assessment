
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics import ndcg_score


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

CORPUS_FILE = ROOT / "data/processed/bm25_corpus.csv"
QUERY_FILE = ROOT / "data/benchmark/queries.csv"
JUDGMENT_FILE = ROOT / "data/benchmark/relevance_judgments.csv"

EMBEDDING_FILE = ROOT / "data/processed/mpnet_document_embeddings.npy"
RESULT_FILE = ROOT / "data/benchmark/mpnet_results.csv"

OUTPUT_DIR = ROOT / "results/mpnet"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Check input files
# --------------------------------------------------

for file_path in [CORPUS_FILE, QUERY_FILE, JUDGMENT_FILE]:
    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")

corpus = pd.read_csv(CORPUS_FILE)
queries = pd.read_csv(QUERY_FILE)
judgments = pd.read_csv(JUDGMENT_FILE)

print("Corpus rows:", len(corpus))
print("Benchmark queries:", len(queries))
print("Relevance judgments:", len(judgments))


# --------------------------------------------------
# 3. Identify the correct column names
# --------------------------------------------------

def find_column(data, candidates, description):
    for column in candidates:
        if column in data.columns:
            return column

    raise ValueError(
        f"Cannot find {description}. "
        f"Available columns: {list(data.columns)}"
    )


document_column = find_column(
    corpus, ["bm25_document"], "document text column"
)

scheme_id_column = find_column(
    corpus, ["scheme_id", "Id", "ID", "id"], "scheme ID column"
)

scheme_name_column = find_column(
    corpus,
    ["scheme_name", "Scholarship", "scheme", "name"],
    "scheme name column"
)

query_text_column = find_column(
    queries, ["query", "query_text"], "query text column"
)

query_id_column = find_column(
    queries, ["query_id"], "query ID column"
)

judgment_query_column = find_column(
    judgments, ["query_id"], "judgment query ID column"
)

judgment_scheme_column = find_column(
    judgments,
    ["scheme_id", "Id", "ID", "id"],
    "judgment scheme ID column"
)

relevance_column = find_column(
    judgments,
    ["relevance", "relevance_score", "relevance_label",
     "relevance_label_numeric"],
    "relevance column"
)


# --------------------------------------------------
# 4. Load the MPNet model
# --------------------------------------------------

print("\nLoading MPNet model...")

model = SentenceTransformer(
    "sentence-transformers/all-mpnet-base-v2"
)

print("MPNet model loaded successfully.")


# --------------------------------------------------
# 5. Generate scheme embeddings
# --------------------------------------------------

documents = corpus[document_column].fillna("").astype(str).tolist()

document_embeddings = model.encode(
    documents,
    convert_to_numpy=True,
    normalize_embeddings=True,
    show_progress_bar=True
)

print("Embedding shape:", document_embeddings.shape)

if document_embeddings.shape[1] != 768:
    raise ValueError("Expected MPNet embeddings with 768 dimensions.")

np.save(EMBEDDING_FILE, document_embeddings)
print("Saved embeddings:", EMBEDDING_FILE)


# --------------------------------------------------
# 6. Generate query embeddings
# --------------------------------------------------

query_texts = (
    queries[query_text_column].fillna("").astype(str).tolist()
)

query_embeddings = model.encode(
    query_texts,
    convert_to_numpy=True,
    normalize_embeddings=True,
    show_progress_bar=True
)


# --------------------------------------------------
# 7. Calculate cosine similarity
# --------------------------------------------------

similarities = query_embeddings @ document_embeddings.T


# --------------------------------------------------
# 8. Retrieve Top-10 schemes
# --------------------------------------------------

results = []

for query_index, query_row in queries.iterrows():

    scores = similarities[query_index]
    top_indices = np.argsort(scores)[::-1][:10]

    for rank, document_index in enumerate(top_indices, start=1):

        results.append({
            "query_id": query_row[query_id_column],
            "query": query_row[query_text_column],
            "rank": rank,
            "scheme_id": corpus.iloc[document_index][scheme_id_column],
            "scheme_name": corpus.iloc[document_index][scheme_name_column],
            "similarity_score": float(scores[document_index])
        })

results_df = pd.DataFrame(results)
results_df.to_csv(RESULT_FILE, index=False)

print("\nSaved retrieval results:", RESULT_FILE)
print("Number of queries:", results_df["query_id"].nunique())
print("Number of results:", len(results_df))
print("\nFirst 10 results:")
print(results_df.head(10).to_string(index=False))


# --------------------------------------------------
# 9. Convert relevance judgments to numeric values
# --------------------------------------------------

judgments = judgments.copy()

judgments["_relevance"] = pd.to_numeric(
    judgments["relevance_score"],
    errors="coerce"
)

judgments = judgments.dropna(subset=["_relevance"])

judgments["query_id"] = (
    judgments["query_id"].astype(str).str.strip()
)
judgments["scheme_id"] = (
    judgments["scheme_id"].astype(str).str.strip()
)

judgments["_relevance"] = judgments["_relevance"].clip(0, 2)

judgments = judgments.drop_duplicates(
    subset=["query_id", "scheme_id"]
)

results_df["query_id"] = (
    results_df["query_id"].astype(str).str.strip()
)
results_df["scheme_id"] = (
    results_df["scheme_id"].astype(str).str.strip()
)

# Merge judgments with retrieved results.
evaluated = results_df.merge(
    judgments[["query_id", "scheme_id", "_relevance"]],
    on=["query_id", "scheme_id"],
    how="left"
)

# --------------------------------------------------
# 10. Calculate metrics using judged results only
# --------------------------------------------------

query_metrics = []
error_rows = []

for query_id, group in evaluated.groupby("query_id", sort=False):

    group = group.sort_values("rank").copy()

    judged = group[group["_relevance"].notna()].copy()
    total_retrieved = len(group)
    judged_count = len(judged)

    coverage = (
        judged_count / total_retrieved
        if total_retrieved else 0
    )

    # Record incomplete judgment coverage.
    if judged_count < total_retrieved:
        error_rows.append({
            "query_id": query_id,
            "query": group["query"].iloc[0],
            "rank": "",
            "scheme_id": "",
            "scheme_name": "",
            "relevance": "",
            "similarity_score": "",
            "observation": (
                f"{total_retrieved - judged_count} of "
                f"{total_retrieved} retrieved schemes are unjudged"
            )
        })

    # Do not calculate metrics for queries with no judgments.
    if judged_count == 0:
        continue

    # These are provisional judged-only metrics.
    # They are NOT standard full-Top-K metrics when coverage
    # is incomplete. Review coverage before reporting them.

    def judged_precision(k):
        topk = judged[judged["rank"] <= k]
        if len(topk) == 0:
            return np.nan
        return float((topk["_relevance"] >= 1).sum() / len(topk))

    def judged_recall(k):
        # Recall denominator uses all independently judged
        # relevant schemes for this query.
        all_judgments = judgments[
            judgments["query_id"] == query_id
        ]
        total_relevant = int(
            (all_judgments["_relevance"] >= 1).sum()
        )

        topk = judged[judged["rank"] <= k]
        found = int((topk["_relevance"] >= 1).sum())

        if total_relevant == 0:
            return np.nan

        return found / total_relevant

    relevant_rows = judged[judged["_relevance"] >= 1]

    if len(relevant_rows):
        first_relevant_rank = int(relevant_rows["rank"].min())
        reciprocal_rank = 1 / first_relevant_rank
    else:
        # No judged relevant result is not proof that
        # the query has no relevant retrieved result.
        reciprocal_rank = np.nan

    def judged_ndcg(k):
        topk = judged[judged["rank"] <= k]
        if topk.empty:
            return np.nan

        # Use the graded relevance values for judged results.
        gains = topk["_relevance"].to_numpy(dtype=float)
        discounts = np.log2(topk["rank"].to_numpy(dtype=float) + 1)
        dcg = float(np.sum((2 ** gains - 1) / discounts))

        ideal = np.sort(
            judgments.loc[
                judgments["query_id"] == query_id,
                "_relevance"
            ].to_numpy(dtype=float)
        )[::-1][:k]

        ideal_discounts = np.log2(np.arange(2, len(ideal) + 2))
        idcg = float(np.sum((2 ** ideal - 1) / ideal_discounts))

        return dcg / idcg if idcg > 0 else np.nan

    query_metrics.append({
        "query_id": query_id,
        "judged_results": judged_count,
        "retrieved_results": total_retrieved,
        "judgment_coverage": coverage,
        "precision@5_judged_only": judged_precision(5),
        "recall@5": judged_recall(5),
        "precision@10_judged_only": judged_precision(10),
        "recall@10": judged_recall(10),
        "reciprocal_rank_judged_only": reciprocal_rank,
        "ndcg@5_judged_only": judged_ndcg(5),
        "ndcg@10_judged_only": judged_ndcg(10)
    })

# --------------------------------------------------
# 11. Save per-query results
# --------------------------------------------------

per_query_df = pd.DataFrame(query_metrics)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

per_query_path = OUTPUT_DIR / "mpnet_per_query.csv"
per_query_df.to_csv(per_query_path, index=False)

print("\nPer-query rows:", len(per_query_df))
print("Saved:", per_query_path)

# --------------------------------------------------
# 12. Save aggregate metrics
# --------------------------------------------------

metric_columns = [
    "precision@5_judged_only",
    "recall@5",
    "precision@10_judged_only",
    "recall@10",
    "reciprocal_rank_judged_only",
    "ndcg@5_judged_only",
    "ndcg@10_judged_only"
]

metric_rows = []

for metric in metric_columns:
    values = (
        per_query_df[metric].dropna()
        if metric in per_query_df.columns
        else pd.Series(dtype=float)
    )

    metric_rows.append({
        "metric": metric,
        "value": float(values.mean()) if len(values) else np.nan,
        "queries_included": int(len(values)),
        "evaluation_note": (
            "Provisional; inspect judgment coverage before reporting"
        )
    })

metrics_df = pd.DataFrame(metric_rows)

metrics_path = OUTPUT_DIR / "mpnet_metrics.csv"
metrics_df.to_csv(metrics_path, index=False)

print("\nSaved:", metrics_path)
print(metrics_df.to_string(index=False))

# --------------------------------------------------
# 13. Save error analysis
# --------------------------------------------------

errors_path = OUTPUT_DIR / "mpnet_errors.csv"

pd.DataFrame(
    error_rows,
    columns=[
        "query_id", "query", "rank", "scheme_id",
        "scheme_name", "relevance", "similarity_score",
        "observation"
    ]
).to_csv(errors_path, index=False)

print("\nSaved:", errors_path)

print("\n========== DAY 13 OUTPUT CHECK ==========")
print("MPNet results:", len(results_df))
print("Queries with at least one judged result:", len(per_query_df))
print("Metrics file exists:", metrics_path.exists())
print("Per-query file exists:", per_query_path.exists())
print("=========================================")