import pandas as pd
from pathlib import Path


BM25_RESULTS = "data/benchmark/bm25_results.csv"
JUDGMENTS = "data/benchmark/relevance_judgments.csv"

OUTPUT_FILE = "data/benchmark/precision_recall_at_10.csv"

# Same threshold used for Precision@5 and Recall@5
RELEVANCE_THRESHOLD = 1


def calculate_metrics_at_10():

    # Load BM25 results
    results = pd.read_csv(BM25_RESULTS)

    # Load relevance judgments
    judgments = pd.read_csv(JUDGMENTS)

    # --------------------------------------------------
    # STEP 1: Keep only Top 10 BM25 results
    # --------------------------------------------------

    top10 = results[
        results["rank"] <= 10
    ].copy()

    # --------------------------------------------------
    # STEP 2: Determine all relevant schemes
    # --------------------------------------------------

    relevant_judgments = judgments[
        judgments["relevance_score"] >= RELEVANCE_THRESHOLD
    ].copy()

    # --------------------------------------------------
    # STEP 3: Count total relevant schemes per query
    # --------------------------------------------------

    total_relevant = (
        relevant_judgments
        .groupby("query_id")
        .size()
        .reset_index(name="total_relevant")
    )

    # --------------------------------------------------
    # STEP 4: Match retrieved Top-10 schemes
    # with relevant schemes
    # --------------------------------------------------

    retrieved_relevant = top10.merge(
        relevant_judgments[
            ["query_id", "scheme_id"]
        ],
        on=["query_id", "scheme_id"],
        how="inner"
    )

    # --------------------------------------------------
    # STEP 5: Count relevant schemes retrieved
    # --------------------------------------------------

    relevant_retrieved = (
        retrieved_relevant
        .groupby("query_id")
        .size()
        .reset_index(
            name="relevant_retrieved_at_10"
        )
    )

    # --------------------------------------------------
    # STEP 6: Combine data
    # --------------------------------------------------

    metrics = total_relevant.merge(
        relevant_retrieved,
        on="query_id",
        how="left"
    )

    # No relevant scheme retrieved = 0
    metrics["relevant_retrieved_at_10"] = (
        metrics["relevant_retrieved_at_10"]
        .fillna(0)
    )

    # --------------------------------------------------
    # STEP 7: Calculate Precision@10
    # --------------------------------------------------

    metrics["precision_at_10"] = (
        metrics["relevant_retrieved_at_10"] / 10
    )

    # --------------------------------------------------
    # STEP 8: Calculate Recall@10
    # --------------------------------------------------

    metrics["recall_at_10"] = (
        metrics["relevant_retrieved_at_10"]
        / metrics["total_relevant"]
    )

    # --------------------------------------------------
    # STEP 9: Calculate mean metrics
    # --------------------------------------------------

    mean_precision = (
        metrics["precision_at_10"].mean()
    )

    mean_recall = (
        metrics["recall_at_10"].mean()
    )

    # --------------------------------------------------
    # STEP 10: Print results
    # --------------------------------------------------

    print("=" * 60)
    print("PRECISION@10 AND RECALL@10 EVALUATION")
    print("=" * 60)

    print(
        f"Relevance threshold: "
        f"relevance_score >= {RELEVANCE_THRESHOLD}"
    )

    print(
        f"Queries evaluated: "
        f"{len(metrics)}"
    )

    print(
        f"Mean Precision@10: "
        f"{mean_precision:.4f}"
    )

    print(
        f"Mean Recall@10: "
        f"{mean_recall:.4f}"
    )

    print("=" * 60)

    # --------------------------------------------------
    # STEP 11: Save results
    # --------------------------------------------------

    Path("data/benchmark").mkdir(
        parents=True,
        exist_ok=True
    )

    metrics.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    calculate_metrics_at_10()