import pandas as pd
from pathlib import Path


BM25_RESULTS = "data/benchmark/bm25_results.csv"
JUDGMENTS = "data/benchmark/relevance_judgments.csv"
OUTPUT_FILE = "data/benchmark/precision_at_5.csv"


# Relevance threshold
# 2 = Relevant
# 1 = Partially Relevant
# 0 = Not Relevant
RELEVANCE_THRESHOLD = 1


def calculate_precision_at_5():

    # Load BM25 results
    results = pd.read_csv(BM25_RESULTS)

    # Load relevance judgments
    judgments = pd.read_csv(JUDGMENTS)

    # Keep only Top 5 results
    top5 = results[results["rank"] <= 5].copy()

    # Merge BM25 results with relevance judgments
    merged = top5.merge(
        judgments[
            ["query_id", "scheme_id", "relevance_score"]
        ],
        on=["query_id", "scheme_id"],
        how="left"
    )

    # Missing judgments are treated as not relevant
    merged["relevance_score"] = (
        merged["relevance_score"]
        .fillna(0)
    )

    # Determine whether each result is relevant
    merged["is_relevant"] = (
        merged["relevance_score"] >= RELEVANCE_THRESHOLD
    )

    # Calculate Precision@5 for each query
    query_results = []

    for query_id, group in merged.groupby("query_id"):

        relevant_count = group["is_relevant"].sum()

        precision = relevant_count / 5

        query_results.append({
            "query_id": query_id,
            "relevant_in_top5": int(relevant_count),
            "precision_at_5": precision
        })

    precision_df = pd.DataFrame(query_results)

    # Calculate overall Precision@5
    mean_precision = precision_df["precision_at_5"].mean()

    print("=" * 60)
    print("PRECISION@5 EVALUATION")
    print("=" * 60)

    print(
        f"Relevance threshold: "
        f"relevance_score >= {RELEVANCE_THRESHOLD}"
    )

    print(
        f"Queries evaluated: "
        f"{len(precision_df)}"
    )

    print(
        f"Mean Precision@5: "
        f"{mean_precision:.4f}"
    )

    print("=" * 60)

    # Save per-query results
    Path("data/benchmark").mkdir(
        parents=True,
        exist_ok=True
    )

    precision_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    calculate_precision_at_5()