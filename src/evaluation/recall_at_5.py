import pandas as pd
from pathlib import Path


BM25_RESULTS = "data/benchmark/bm25_results.csv"
JUDGMENTS = "data/benchmark/relevance_judgments.csv"
OUTPUT_FILE = "data/benchmark/recall_at_5.csv"


# Same threshold used for Precision@5
# 2 = Relevant
# 1 = Partially Relevant
# 0 = Not Relevant
RELEVANCE_THRESHOLD = 1


def calculate_recall_at_5():

    # Load BM25 results
    results = pd.read_csv(BM25_RESULTS)

    # Load relevance judgments
    judgments = pd.read_csv(JUDGMENTS)

    # Keep only Top 5 BM25 results
    top5 = results[results["rank"] <= 5].copy()

    # Determine all relevant schemes for every query
    relevant_judgments = judgments[
        judgments["relevance_score"] >= RELEVANCE_THRESHOLD
    ].copy()

    # Number of relevant schemes for each query
    total_relevant = (
        relevant_judgments
        .groupby("query_id")
        .size()
        .reset_index(name="total_relevant")
    )

    # Match BM25 Top-5 results with relevance judgments
    retrieved = top5.merge(
        relevant_judgments[
            ["query_id", "scheme_id"]
        ],
        on=["query_id", "scheme_id"],
        how="inner"
    )

    # Count relevant schemes retrieved in Top 5
    retrieved_relevant = (
        retrieved
        .groupby("query_id")
        .size()
        .reset_index(name="relevant_retrieved_at_5")
    )

    # Combine totals
    recall_df = total_relevant.merge(
        retrieved_relevant,
        on="query_id",
        how="left"
    )

    # Queries where no relevant result was retrieved get zero
    recall_df["relevant_retrieved_at_5"] = (
        recall_df["relevant_retrieved_at_5"]
        .fillna(0)
    )

    # Calculate Recall@5
    recall_df["recall_at_5"] = (
        recall_df["relevant_retrieved_at_5"]
        / recall_df["total_relevant"]
    )

    # Overall mean Recall@5
    mean_recall = recall_df["recall_at_5"].mean()

    print("=" * 60)
    print("RECALL@5 EVALUATION")
    print("=" * 60)

    print(
        f"Relevance threshold: "
        f"relevance_score >= {RELEVANCE_THRESHOLD}"
    )

    print(
        f"Queries evaluated: "
        f"{len(recall_df)}"
    )

    print(
        f"Mean Recall@5: "
        f"{mean_recall:.4f}"
    )

    print("=" * 60)

    # Save results
    Path("data/benchmark").mkdir(
        parents=True,
        exist_ok=True
    )

    recall_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    calculate_recall_at_5()