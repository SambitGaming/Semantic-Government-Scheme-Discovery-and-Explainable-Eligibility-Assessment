import pandas as pd
import math
from pathlib import Path


BM25_RESULTS = "data/benchmark/bm25_results.csv"
JUDGMENTS = "data/benchmark/relevance_judgments.csv"

OUTPUT_FILE = "results/bm25/bm25_per_query.csv"

RELEVANCE_THRESHOLD = 1


def dcg(scores, k):
    """Calculate DCG@k."""
    total = 0.0

    for rank, relevance in enumerate(scores[:k], start=1):
        gain = (2 ** relevance) - 1
        discount = math.log2(rank + 1)

        total += gain / discount

    return total


def calculate_ndcg(actual_scores, ideal_scores, k):
    """Calculate nDCG@k."""

    actual_dcg = dcg(actual_scores, k)
    ideal_dcg = dcg(ideal_scores, k)

    if ideal_dcg == 0:
        return 0.0

    return actual_dcg / ideal_dcg


def calculate_metrics():

    # --------------------------------------------------
    # Load data
    # --------------------------------------------------

    results = pd.read_csv(BM25_RESULTS)
    judgments = pd.read_csv(JUDGMENTS)

    # Make sure relevance_score is numeric
    judgments["relevance_score"] = pd.to_numeric(
        judgments["relevance_score"],
        errors="coerce"
    ).fillna(0)

    # --------------------------------------------------
    # Merge BM25 results with judgments
    # --------------------------------------------------

    merged = results.merge(
        judgments[
            ["query_id", "scheme_id", "relevance_score"]
        ],
        on=["query_id", "scheme_id"],
        how="left"
    )

    # Unjudged retrieved schemes = 0
    merged["relevance_score"] = (
        merged["relevance_score"]
        .fillna(0)
    )

    merged["relevance_score"] = (
        merged["relevance_score"]
        .astype(float)
    )

    # --------------------------------------------------
    # All queries with relevance judgments
    # --------------------------------------------------

    query_ids = (
        judgments["query_id"]
        .drop_duplicates()
        .tolist()
    )

    per_query = []

    # --------------------------------------------------
    # Process each query
    # --------------------------------------------------

    for query_id in query_ids:

        query_results = merged[
            merged["query_id"] == query_id
        ].sort_values("rank")

        query_judgments = judgments[
            judgments["query_id"] == query_id
        ]

        # All relevant schemes according to threshold
        relevant_judgments = query_judgments[
            query_judgments["relevance_score"]
            >= RELEVANCE_THRESHOLD
        ]

        total_relevant = len(
            relevant_judgments
        )

        # --------------------------------------------------
        # Precision@5
        # --------------------------------------------------

        top5 = query_results[
            query_results["rank"] <= 5
        ]

        relevant_top5 = (
            top5["relevance_score"]
            >= RELEVANCE_THRESHOLD
        ).sum()

        precision_at_5 = (
            relevant_top5 / 5
        )

        # --------------------------------------------------
        # Recall@5
        # --------------------------------------------------

        if total_relevant > 0:
            recall_at_5 = (
                relevant_top5 /
                total_relevant
            )
        else:
            recall_at_5 = 0.0

        # --------------------------------------------------
        # Precision@10
        # --------------------------------------------------

        top10 = query_results[
            query_results["rank"] <= 10
        ]

        relevant_top10 = (
            top10["relevance_score"]
            >= RELEVANCE_THRESHOLD
        ).sum()

        precision_at_10 = (
            relevant_top10 / 10
        )

        # --------------------------------------------------
        # Recall@10
        # --------------------------------------------------

        if total_relevant > 0:
            recall_at_10 = (
                relevant_top10 /
                total_relevant
            )
        else:
            recall_at_10 = 0.0

        # --------------------------------------------------
        # MRR
        # --------------------------------------------------

        relevant_ranks = top10[
            top10["relevance_score"]
            >= RELEVANCE_THRESHOLD
        ]["rank"]

        if len(relevant_ranks) > 0:
            first_relevant_rank = (
                relevant_ranks.min()
            )

            mrr = 1 / first_relevant_rank

        else:
            mrr = 0.0

        # --------------------------------------------------
        # nDCG
        # --------------------------------------------------

        actual_scores = (
            top10["relevance_score"]
            .tolist()
        )

        ideal_scores = sorted(
            query_judgments[
                "relevance_score"
            ].tolist(),
            reverse=True
        )

        ndcg_at_5 = calculate_ndcg(
            actual_scores,
            ideal_scores,
            5
        )

        ndcg_at_10 = calculate_ndcg(
            actual_scores,
            ideal_scores,
            10
        )

        # --------------------------------------------------
        # Save query metrics
        # --------------------------------------------------

        per_query.append({
            "query_id": query_id,
            "Precision@5": precision_at_5,
            "Recall@5": recall_at_5,
            "Precision@10": precision_at_10,
            "Recall@10": recall_at_10,
            "MRR": mrr,
            "nDCG@5": ndcg_at_5,
            "nDCG@10": ndcg_at_10
        })

    # --------------------------------------------------
    # Create DataFrame
    # --------------------------------------------------

    output_df = pd.DataFrame(
        per_query
    )

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

    output_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------
    # Print summary
    # --------------------------------------------------

    print("=" * 60)
    print("BM25 PER-QUERY EVALUATION")
    print("=" * 60)

    print(
        "Queries evaluated:",
        len(output_df)
    )

    print(
        "Relevance threshold:",
        f"relevance_score >= {RELEVANCE_THRESHOLD}"
    )

    print()
    print("Average metrics:")
    print(
        output_df[
            [
                "Precision@5",
                "Recall@5",
                "Precision@10",
                "Recall@10",
                "MRR",
                "nDCG@5",
                "nDCG@10"
            ]
        ].mean()
    )

    print()
    print(
        "Saved to:",
        OUTPUT_FILE
    )

    print("=" * 60)


if __name__ == "__main__":
    calculate_metrics()