
from pathlib import Path
import pandas as pd
from sentence_transformers import SentenceTransformer

# 1. Set project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent

QUERY_FILE = PROJECT_DIR / "data" / "benchmark" / "queries.csv"
CORPUS_FILE = PROJECT_DIR / "data" / "processed" / "retrieval_corpus.csv"
OUTPUT_FILE = PROJECT_DIR / "data" / "benchmark" / "minilm_ranked_results.csv"

# 2. Check that the input files exist
if not QUERY_FILE.exists():
    raise FileNotFoundError(f"Queries not found: {QUERY_FILE}")

if not CORPUS_FILE.exists():
    raise FileNotFoundError(f"Corpus not found: {CORPUS_FILE}")

# 3. Load benchmark queries and scheme documents
queries = pd.read_csv(QUERY_FILE).fillna("")
corpus = pd.read_csv(CORPUS_FILE).fillna("")

if "query_text" not in queries.columns:
    raise ValueError("benchmark_queries.csv must contain query_text")

if "retrieval_text" not in corpus.columns:
    raise ValueError("retrieval_corpus.csv must contain retrieval_text")

if "scheme_name" not in corpus.columns:
    raise ValueError("retrieval_corpus.csv must contain scheme_name")

queries = queries[queries["query_text"].str.strip() != ""].reset_index(drop=True)
corpus = corpus[corpus["retrieval_text"].str.strip() != ""].reset_index(drop=True)

if queries.empty or corpus.empty:
    raise ValueError("Queries or scheme corpus is empty.")

print("Queries loaded:", len(queries))
print("Schemes loaded:", len(corpus))

# 4. Load the same MiniLM model used for your Day 12 experiment
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# 5. Encode scheme documents and benchmark queries
# Normalization allows dot product to calculate cosine similarity.
document_embeddings = model.encode(
    corpus["retrieval_text"].tolist(),
    normalize_embeddings=True,
    convert_to_numpy=True
)

query_embeddings = model.encode(
    queries["query_text"].tolist(),
    normalize_embeddings=True,
    convert_to_numpy=True
)

print("Query and document embeddings created.")

# 6. Calculate cosine similarity for every query and scheme
similarities = query_embeddings @ document_embeddings.T

# 7. Rank schemes for each query
results = []

for query_index, query_row in queries.iterrows():
    ranked_indices = similarities[query_index].argsort()[::-1]

    for rank, document_index in enumerate(ranked_indices, start=1):
        scheme = corpus.iloc[document_index]

        results.append({
            "query_id": query_row.get("query_id", query_index + 1),
            "query_text": query_row["query_text"],
            "rank": rank,
            "scheme_name": scheme["scheme_name"],
            "similarity": round(
                float(similarities[query_index, document_index]), 4
            )
        })

# 8. Save all ranked results
results_df = pd.DataFrame(results)
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
results_df.to_csv(OUTPUT_FILE, index=False)

print("\nRanking completed successfully!")
print("Output saved to:", OUTPUT_FILE)

# 9. Display the top 3 schemes for each query
print("\nTOP 3 SCHEMES PER QUERY")

for query_id, group in results_df.groupby("query_id", sort=False):
    print(f"\nQuery ID: {query_id}")
    print(group.head(3)[
        ["rank", "scheme_name", "similarity"]
    ].to_string(index=False))