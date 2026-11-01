
from pathlib import Path
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

CORPUS_FILE = ROOT / "data" / "processed" / "bm25_corpus.csv"
QUERIES_FILE = ROOT / "data" / "benchmark" / "queries.csv"
JUDGMENTS_FILE = ROOT / "data" / "benchmark" / "relevance_judgments.csv"

RESULTS_FILE = ROOT / "data" / "benchmark" / "minilm_results.csv"
EMBEDDINGS_FILE = ROOT / "data" / "processed" / "minilm_document_embeddings.npy"

OUTPUT_DIR = ROOT / "results" / "minilm"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 10

# --------------------------------------------------
# 2. Load the existing corpus
# --------------------------------------------------

if not CORPUS_FILE.exists():
    raise FileNotFoundError(f"Corpus not found: {CORPUS_FILE}")

corpus = pd.read_csv(CORPUS_FILE)

def find_column(df, candidates, description):
    for name in candidates:
        if name in df.columns:
            return name
    raise ValueError(
        f"Cannot find {description}. Available columns: "
        f"{list(df.columns)}"
    )

scheme_id_col = find_column(
    corpus, ["scheme_id", "candidate_id", "ID", "Id"],
    "scheme ID column"
)
scheme_name_col = find_column(
    corpus, ["scheme_name", "Scholarship", "scheme", "title"],
    "scheme name column"
)
document_col = find_column(
    corpus, ["bm25_document", "retrieval_text", "document_text"],
    "scheme document text column"
)

corpus = corpus.dropna(subset=[scheme_id_col]).reset_index(drop=True)
corpus[document_col] = corpus[document_col].fillna("").astype(str)

documents = corpus[document_col].tolist()

if not documents:
    raise ValueError("The scheme corpus is empty.")

print("Schemes loaded:", len(corpus))

# --------------------------------------------------
# 3. Load MiniLM and create scheme embeddings
# --------------------------------------------------

print("Loading MiniLM model...")
model = SentenceTransformer(MODEL_NAME)

print("Creating scheme embeddings...")
document_embeddings = model.encode(
    documents,
    convert_to_numpy=True,
    normalize_embeddings=True,
    show_progress_bar=True
)

print("Embedding shape:", document_embeddings.shape)

np.save(EMBEDDINGS_FILE, document_embeddings)
print("Saved embeddings:", EMBEDDINGS_FILE)

# --------------------------------------------------
# 4. Load the existing benchmark queries
# --------------------------------------------------

if not QUERIES_FILE.exists():
    raise FileNotFoundError(f"Queries not found: {QUERIES_FILE}")

queries = pd.read_csv(QUERIES_FILE)

query_id_col = find_column(
    queries, ["query_id"], "query ID column"
)
query_text_col = find_column(
    queries, ["query", "query_text"], "query text column"
)

queries[query_text_col] = (
    queries[query_text_col].fillna("").astype(str)
)

query_embeddings = model.encode(
    queries[query_text_col].tolist(),
    convert_to_numpy=True,
    normalize_embeddings=True,
    show_progress_bar=True
)

# --------------------------------------------------
# 5. Calculate similarity and rank schemes
# --------------------------------------------------

all_results = []

for i, query_row in queries.iterrows():
    # Normalized embeddings: dot product = cosine similarity
    scores = query_embeddings[i] @ document_embeddings.T

    ranked_indices = np.argsort(-scores, kind="stable")[:TOP_K]

    for rank, idx in enumerate(ranked_indices, start=1):
        all_results.append({
            "query_id": query_row[query_id_col],
            "rank": rank,
            "scheme_id": corpus.iloc[idx][scheme_id_col],
            "scheme_name": corpus.iloc[idx][scheme_name_col],
            "similarity_score": float(scores[idx])
        })

results = pd.DataFrame(all_results)
results.to_csv(RESULTS_FILE, index=False)

print("Saved retrieval results:", RESULTS_FILE)
print("Total result rows:", len(results))

# --------------------------------------------------
# 6. Load existing relevance judgments
# --------------------------------------------------

if not JUDGMENTS_FILE.exists():
    raise FileNotFoundError(
        f"Judgments not found: {JUDGMENTS_FILE}"
    )

judgments = pd.read_csv(JUDGMENTS_FILE)

if judgments.empty:
    raise ValueError(
        "Your relevance_judgments.csv is empty. "
        "Complete judgments before calculating metrics."
    )

judgment_query_col = find_column(
    judgments, ["query_id"], "judgment query ID"
)
judgment_scheme_col = find_column(
    judgments, ["scheme_id", "candidate_id", "ID", "Id"],
    "judgment scheme ID"
)

if "relevance_score" in judgments.columns:
    rel_col = "relevance_score"
elif "relevance_label" in judgments.columns:
    rel_col = "relevance_label"
elif "relevance" in judgments.columns:
    rel_col = "relevance"
else:
    raise ValueError(
        "Judgments need relevance_score, relevance_label, "
        "or relevance."
    )

def convert_relevance(value):
    if pd.isna(value):
        return np.nan
    if isinstance(value, str):
        value = value.strip().lower()
        labels = {
            "relevant": 2,
            "partially relevant": 1,
            "partially_relevant": 1,
            "not relevant": 0,
            "not_relevant": 0
        }
        if value in labels:
            return labels[value]
    try:
        score = float(value)
        if score in (0, 1, 2):
            return int(score)
    except (ValueError, TypeError):
        pass
    raise ValueError(f"Unknown relevance value: {value}")

judgments = judgments.copy()
judgments["_rel"] = judgments[rel_col].map(convert_relevance)

judgments = judgments.dropna(subset=["_rel"])
judgments["_rel"] = judgments["_rel"].astype(int)

# Use a consistent string type for joining IDs.
results["_qid"] = results["query_id"].astype(str)
results["_sid"] = results["scheme_id"].astype(str)
judgments["_qid"] = judgments[judgment_query_col].astype(str)
judgments["_sid"] = judgments[judgment_scheme_col].astype(str)

# Remove duplicate judgments for the same query-scheme pair.
judgments = judgments.drop_duplicates(
    subset=["_qid", "_sid"], keep="last"
)

# --------------------------------------------------
# 7. Join retrieval results with judgments
# --------------------------------------------------

evaluated = results.merge(
    judgments[["_qid", "_sid", "_rel"]],
    on=["_qid", "_sid"],
    how="left"
)

# Unjudged results are temporarily treated as non-relevant.
# For valid evaluation, judge the retrieved results first.
evaluated["_rel"] = evaluated["_rel"].fillna(0).astype(int)

# --------------------------------------------------
# 8. Calculate ranking metrics
# --------------------------------------------------

def dcg(relevances):
    relevances = np.asarray(relevances, dtype=float)
    discounts = np.log2(np.arange(2, len(relevances) + 2))
    gains = (2 ** relevances) - 1
    return float(np.sum(gains / discounts))

def evaluate_query(group, query_id):
    group = group.sort_values("rank")
    rel = group["_rel"].to_numpy()
    output = {"query_id": query_id}

    # Binary relevance: Relevant OR Partially Relevant.
    binary = (rel >= 1).astype(int)

    # Only judged relevant schemes count in the denominator.
    # Incomplete judgments can make recall misleading.
    q_judgments = judgments[judgments["_qid"] == str(query_id)]
    total_relevant = int((q_judgments["_rel"] >= 1).sum())

    for k in (5, 10):
        top_rel = rel[:k]
        top_binary = binary[:k]

        output[f"precision@{k}"] = (
            float(top_binary.sum() / k) if len(top_binary) else 0.0
        )
        output[f"recall@{k}"] = (
            float(top_binary.sum() / total_relevant)
            if total_relevant > 0 else np.nan
        )

        ideal = np.sort(q_judgments["_rel"].to_numpy())[::-1][:k]
        ideal_dcg = dcg(ideal)
        output[f"ndcg@{k}"] = (
            dcg(top_rel) / ideal_dcg if ideal_dcg > 0 else np.nan
        )

    relevant_ranks = group.loc[group["_rel"] >= 1, "rank"]
    output["reciprocal_rank"] = (
        1.0 / float(relevant_ranks.iloc[0])
        if not relevant_ranks.empty else 0.0
    )

    return output

per_query_rows = []

for query_id, group in evaluated.groupby("query_id", sort=False):
    per_query_rows.append(evaluate_query(group, query_id))

per_query = pd.DataFrame(per_query_rows)

metric_names = [
    "precision@5", "recall@5",
    "precision@10", "recall@10",
    "reciprocal_rank", "ndcg@5", "ndcg@10"
]

metrics = pd.DataFrame([
    {
        "metric": metric,
        "value": per_query[metric].mean()
    }
    for metric in metric_names
])

metrics_file = OUTPUT_DIR / "minilm_metrics.csv"
per_query_file = OUTPUT_DIR / "minilm_per_query.csv"

metrics.to_csv(metrics_file, index=False)
per_query.to_csv(per_query_file, index=False)

# --------------------------------------------------
# 9. Save potential retrieval errors for inspection
# --------------------------------------------------

error_rows = evaluated[
    (evaluated["_rel"] == 0) |
    ((evaluated["_rel"] >= 1) & (evaluated["rank"] > 5))
].copy()

query_lookup = queries.set_index(
    queries[query_id_col].astype(str)
)[query_text_col].to_dict()

error_rows["query"] = error_rows["_qid"].map(query_lookup)
error_rows["relevance"] = error_rows["_rel"]
error_rows["observation"] = error_rows.apply(
    lambda row: (
        "Potentially irrelevant result; verify judgment"
        if row["_rel"] == 0
        else "Relevant result ranked below position 5"
    ),
    axis=1
)

error_columns = [
    "query_id", "query", "rank", "scheme_id",
    "relevance", "similarity_score", "observation"
]

errors_file = OUTPUT_DIR / "minilm_errors.csv"
error_rows[error_columns].to_csv(errors_file, index=False)

# --------------------------------------------------
# 10. Print summary
# --------------------------------------------------

print("\nMINILM EVALUATION METRICS")
print(metrics.to_string(index=False))

print("\nOutput files created:")
print(RESULTS_FILE)
print(EMBEDDINGS_FILE)
print(metrics_file)
print(per_query_file)
print(errors_file)

print("\nMiniLM pipeline completed.")