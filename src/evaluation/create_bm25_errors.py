import pandas as pd
from pathlib import Path


OUTPUT_FILE = "results/bm25/bm25_errors.csv"

# --------------------------------------------------
# Load files
# --------------------------------------------------

missed = pd.read_csv(
    "results/bm25/error_missed_relevant.csv"
)

rank1 = pd.read_csv(
    "results/bm25/error_irrelevant_rank1.csv"
)

low_rank = pd.read_csv(
    "results/bm25/error_relevant_rank9_10.csv"
)

queries = pd.read_csv(
    "data/benchmark/queries.csv"
)


# --------------------------------------------------
# Create query_id -> query_text mapping
# --------------------------------------------------

query_map = dict(
    zip(
        queries["query_id"],
        queries["query_text"]
    )
)


errors = []


# --------------------------------------------------
# CASE 1 — Relevant scheme missed from Top-10
# --------------------------------------------------

for _, row in missed.iterrows():

    query_id = row["query_id"]

    errors.append({
        "query_id": query_id,
        "query": query_map.get(
            query_id,
            ""
        ),
        "rank": "Not retrieved",
        "scheme_id": row["scheme_id"],
        "relevance": row["relevance_score"],
        "observation":
            "Relevant scheme was not retrieved within Top-10"
    })


# --------------------------------------------------
# CASE 2 — Irrelevant scheme at Rank 1
# --------------------------------------------------

for _, row in rank1.iterrows():

    query_id = row["query_id"]

    errors.append({
        "query_id": query_id,
        "query": query_map.get(
            query_id,
            ""
        ),
        "rank": row["rank"],
        "scheme_id": row["scheme_id"],
        "relevance": row["relevance_score"],
        "observation":
            "Irrelevant scheme ranked first despite lexical overlap"
    })


# --------------------------------------------------
# CASE 3 — Relevant scheme ranked 9 or 10
# --------------------------------------------------

for _, row in low_rank.iterrows():

    query_id = row["query_id"]

    errors.append({
        "query_id": query_id,
        "query": query_map.get(
            query_id,
            ""
        ),
        "rank": row["rank"],
        "scheme_id": row["scheme_id"],
        "relevance": row["relevance_score"],
        "observation":
            "Relevant scheme was retrieved but ranked too low"
    })


# --------------------------------------------------
# Create DataFrame
# --------------------------------------------------

errors_df = pd.DataFrame(
    errors,
    columns=[
        "query_id",
        "query",
        "rank",
        "scheme_id",
        "relevance",
        "observation"
    ]
)


# Remove duplicates
errors_df = errors_df.drop_duplicates()


# --------------------------------------------------
# Create output directory
# --------------------------------------------------

Path("results/bm25").mkdir(
    parents=True,
    exist_ok=True
)


# --------------------------------------------------
# Save
# --------------------------------------------------

errors_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# --------------------------------------------------
# Print summary
# --------------------------------------------------

print("=" * 60)
print("BM25 ERROR ANALYSIS SAVED")
print("=" * 60)

print(
    "Total error cases:",
    len(errors_df)
)

print(
    "Saved to:",
    OUTPUT_FILE
)

print("=" * 60)