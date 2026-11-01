import pandas as pd
import math
from pathlib import Path


BM25_RESULTS = "data/benchmark/bm25_results.csv"
JUDGMENTS = "data/benchmark/relevance_judgments.csv"

OUTPUT_FILE = "data/benchmark/ndcg_results.csv"

# Graded relevance:
# 2 = Relevant
# 1 = Partially Relevant
# 0 = Not Relevant
RELEVANCE_THRESHOLD = 1


def dcg(relevance_scores, k):
    """
    Calculate Discounted Cumulative Gain at k.
    """

    score = 0.0

    for rank, relevance in enumerate(
        relevance_scores[:k],
        start=1
    ):

        gain = (2 ** relevance) - 1

        discount = math.log2(rank + 1)

        score += gain / discount

    return score


def ndcg(relevance_scores, ideal_scores, k):
    """
    Calculate normalized DCG at k.
    """

    actual_dcg = dcg(
        relevance_scores,
        k
    )

    ideal_dcg = dcg(
        ideal_scores,
        k
    )

    if ideal_dcg == 0:
        return 0.0

    return actual_dcg / ideal_dcg


def calculate_ndcg():

    # --------------------------------------------------
    # Load files
    # --------------------------------------------------

    results = pd.read_csv(
        BM25_RESULTS
    )

    judgments = pd.read_csv(
        JUDGMENTS
    )

    # --------------------------------------------------
    # Keep Top 10
    # --------------------------------------------------

    top10 = results[
        results["rank"] <= 10
    ].copy()

    # --------------------------------------------------
    # Merge BM25 results with relevance judgments
    # --------------------------------------------------

    merged = top10.merge(
        judgments[
            [
                "query_id",
                "scheme_id",
                "relevance_score"
            ]
        ],
        on=[
            "query_id",
            "scheme_id"
        ],
        how="left"
    )

    # Missing judgments = 0 relevance
    merged["relevance_score"] = (
        merged["relevance_score"]
        .fillna(0)
    )

    # Make sure relevance is numeric
    merged["relevance_score"] = (
        merged["relevance_score"]
        .astype(float)
    )

    # --------------------------------------------------
    # Determine which queries have relevant judgments
    # --------------------------------------------------

    relevant_queries = (
        judgments[
            judgments["relevance_score"]
            >= RELEVANCE_THRESHOLD
        ]["query_id"]
        .unique()
    )

    merged = merged[
        merged["query_id"].isin(
            relevant_queries
        )
    ]

    # --------------------------------------------------
    # Calculate nDCG for each query
    # --------------------------------------------------

    query_results = []

    for query_id, group in merged.groupby(
        "query_id"
    ):

        # Sort by BM25 ranking
        group = group.sort_values(
            "rank"
        )

        # Actual BM25 ranking
        actual_scores = (
            group["relevance_score"]
            .tolist()
        )

        # --------------------------------------------------
        # Get all relevance judgments for this query
        # --------------------------------------------------

        query_judgments = judgments[
            judgments["query_id"] == query_id
        ]

        all_scores = (
            query_judgments[
                "relevance_score"
            ]
            .astype(float)
            .tolist()
        )

        # Ideal ranking
        ideal_scores = sorted(
            all_scores,
            reverse=True
        )

        # --------------------------------------------------
        # Calculate nDCG@5
        # --------------------------------------------------

        ndcg5 = ndcg(
            actual_scores,
            ideal_scores,
            5
        )

        # --------------------------------------------------
        # Calculate nDCG@10
        # --------------------------------------------------

        ndcg10 = ndcg(
            actual_scores,
            ideal_scores,
            10
        )

        query_results.append({
            "query_id": query_id,
            "ndcg_at_5": ndcg5,
            "ndcg_at_10": ndcg10
        })

    # --------------------------------------------------
    # Create DataFrame
    # --------------------------------------------------

    ndcg_df = pd.DataFrame(
        query_results
    )

    # --------------------------------------------------
    # Calculate mean nDCG
    # --------------------------------------------------

    mean_ndcg5 = (
        ndcg_df["ndcg_at_5"]
        .mean()
    )

    mean_ndcg10 = (
        ndcg_df["ndcg_at_10"]
        .mean()
    )

    # --------------------------------------------------
    # Print results
    # --------------------------------------------------

    print("=" * 60)
    print("nDCG EVALUATION")
    print("=" * 60)

    print(
        "Relevance levels:"
    )

    print(
        "2 = Relevant"
    )

    print(
        "1 = Partially Relevant"
    )

    print(
        "0 = Not Relevant"
    )

    print(
        f"Queries evaluated: "
        f"{len(ndcg_df)}"
    )

    print(
        f"Mean nDCG@5: "
        f"{mean_ndcg5:.4f}"
    )

    print(
        f"Mean nDCG@10: "
        f"{mean_ndcg10:.4f}"
    )

    print("=" * 60)

    # --------------------------------------------------
    # Save results
    # --------------------------------------------------

    Path(
        "data/benchmark"
    ).mkdir(
        parents=True,
        exist_ok=True
    )

    ndcg_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Saved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    calculate_ndcg()