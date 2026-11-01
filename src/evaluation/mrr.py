import pandas as pd
from pathlib import Path


BM25_RESULTS = "data/benchmark/bm25_results.csv"
JUDGMENTS = "data/benchmark/relevance_judgments.csv"

OUTPUT_FILE = "data/benchmark/mrr_results.csv"

# Same relevance definition used in previous metrics
# 2 = Relevant
# 1 = Partially Relevant
# 0 = Not Relevant
RELEVANCE_THRESHOLD = 1


def calculate_mrr():

    # Load BM25 results
    results = pd.read_csv(BM25_RESULTS)

    # Load relevance judgments
    judgments = pd.read_csv(JUDGMENTS)

    # --------------------------------------------------
    # STEP 1: Keep Top-10 results
    # --------------------------------------------------

    top10 = results[
        results["rank"] <= 10
    ].copy()

    # --------------------------------------------------
    # STEP 2: Keep relevant judgments
    # --------------------------------------------------

    relevant_judgments = judgments[
        judgments["relevance_score"] >= RELEVANCE_THRESHOLD
    ].copy()

    # --------------------------------------------------
    # STEP 3: Match BM25 results with relevant schemes
    # --------------------------------------------------

    relevant_results = top10.merge(
        relevant_judgments[
            ["query_id", "scheme_id"]
        ],
        on=["query_id", "scheme_id"],
        how="inner"
    )

    # --------------------------------------------------
    # STEP 4: Find first relevant rank for each query
    # --------------------------------------------------

    first_relevant = (
        relevant_results
        .groupby("query_id")["rank"]
        .min()
        .reset_index(name="first_relevant_rank")
    )

    # --------------------------------------------------
    # STEP 5: Get all evaluated queries
    # --------------------------------------------------

    queries = relevant_judgments[
        ["query_id"]
    ].drop_duplicates()

    # --------------------------------------------------
    # STEP 6: Include queries with no relevant result
    # --------------------------------------------------

    mrr_df = queries.merge(
        first_relevant,
        on="query_id",
        how="left"
    )

    # No relevant result in Top-10 = RR of 0
    mrr_df["reciprocal_rank"] = (
        1 / mrr_df["first_relevant_rank"]
    )

    mrr_df["reciprocal_rank"] = (
        mrr_df["reciprocal_rank"]
        .fillna(0)
    )

    # --------------------------------------------------
    # STEP 7: Calculate MRR
    # --------------------------------------------------

    mrr = mrr_df["reciprocal_rank"].mean()

    # --------------------------------------------------
    # STEP 8: Print results
    # --------------------------------------------------

    print("=" * 60)
    print("MRR EVALUATION")
    print("=" * 60)

    print(
        f"Relevance threshold: "
        f"relevance_score >= {RELEVANCE_THRESHOLD}"
    )

    print(
        f"Queries evaluated: "
        f"{len(mrr_df)}"
    )

    print(
        f"Mean Reciprocal Rank (MRR): "
        f"{mrr:.4f}"
    )

    print("=" * 60)

    # --------------------------------------------------
    # STEP 9: Save results
    # --------------------------------------------------

    Path("data/benchmark").mkdir(
        parents=True,
        exist_ok=True
    )

    mrr_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    calculate_mrr()