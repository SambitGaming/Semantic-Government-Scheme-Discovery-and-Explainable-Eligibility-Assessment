import pandas as pd
from pathlib import Path


BM25_RESULTS = "data/benchmark/bm25_results.csv"
JUDGMENTS = "data/benchmark/relevance_judgments.csv"
QUERIES = "data/benchmark/queries.csv"

OUTPUT_DIR = "results/bm25"


RELEVANCE_THRESHOLD = 1


def main():

    # --------------------------------------------------
    # Load files
    # --------------------------------------------------

    results = pd.read_csv(BM25_RESULTS)
    judgments = pd.read_csv(JUDGMENTS)
    queries = pd.read_csv(QUERIES)

    judgments["relevance_score"] = pd.to_numeric(
        judgments["relevance_score"],
        errors="coerce"
    ).fillna(0)

    # --------------------------------------------------
    # Add relevance to BM25 results
    # --------------------------------------------------

    merged = results.merge(
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

    # No judgment = not relevant for retrieval analysis
    merged["relevance_score"] = (
        merged["relevance_score"]
        .fillna(0)
    )

    # --------------------------------------------------
    # CASE 1
    # Relevant schemes missing from Top-10
    # --------------------------------------------------

    relevant = judgments[
        judgments["relevance_score"]
        >= RELEVANCE_THRESHOLD
    ]

    retrieved_top10 = merged[
        merged["rank"] <= 10
    ]

    retrieved_pairs = set(
        zip(
            retrieved_top10["query_id"],
            retrieved_top10["scheme_id"]
        )
    )

    missed_rows = []

    for _, row in relevant.iterrows():

        pair = (
            row["query_id"],
            row["scheme_id"]
        )

        if pair not in retrieved_pairs:

            missed_rows.append({
                "query_id": row["query_id"],
                "scheme_id": row["scheme_id"],
                "relevance_score": row["relevance_score"]
            })

    missed_df = pd.DataFrame(
        missed_rows
    )

    # Add query text
    if not missed_df.empty:
        missed_df = missed_df.merge(
            queries[
                ["query_id", "query_text"]
            ],
            on="query_id",
            how="left"
        )

    # --------------------------------------------------
    # CASE 2
    # Irrelevant scheme at Rank 1
    # --------------------------------------------------

    rank1 = merged[
        merged["rank"] == 1
    ].copy()

    irrelevant_rank1 = rank1[
        rank1["relevance_score"] == 0
    ].copy()

    irrelevant_rank1 = irrelevant_rank1.merge(
        queries[
            ["query_id", "query_text"]
        ],
        on="query_id",
        how="left"
    )

    # --------------------------------------------------
    # CASE 3
    # Relevant scheme at Rank 9 or 10
    # --------------------------------------------------

    low_rank_relevant = merged[
        (merged["rank"].isin([9, 10])) &
        (merged["relevance_score"] >= RELEVANCE_THRESHOLD)
    ].copy()

    low_rank_relevant = low_rank_relevant.merge(
        queries[
            ["query_id", "query_text"]
        ],
        on="query_id",
        how="left"
    )

    # --------------------------------------------------
    # CASE 4
    # Ambiguous queries
    # --------------------------------------------------

    ambiguous_types = [
        "Ambiguous",
        "Underspecified"
    ]

    ambiguous_queries = queries[
        queries["query_type"].isin(
            ambiguous_types
        )
    ].copy()

    ambiguous_results = merged.merge(
        ambiguous_queries[
            ["query_id", "query_text", "query_type"]
        ],
        on=[
            "query_id",
            "query_text"
        ],
        how="inner"
    )

    # --------------------------------------------------
    # Create output directory
    # --------------------------------------------------

    Path(OUTPUT_DIR).mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------
    # Save error files
    # --------------------------------------------------

    missed_df.to_csv(
        f"{OUTPUT_DIR}/error_missed_relevant.csv",
        index=False
    )

    irrelevant_rank1.to_csv(
        f"{OUTPUT_DIR}/error_irrelevant_rank1.csv",
        index=False
    )

    low_rank_relevant.to_csv(
        f"{OUTPUT_DIR}/error_relevant_rank9_10.csv",
        index=False
    )

    ambiguous_results.to_csv(
        f"{OUTPUT_DIR}/error_ambiguous_queries.csv",
        index=False
    )

    # --------------------------------------------------
    # Print summary
    # --------------------------------------------------

    print("=" * 65)
    print("BM25 ERROR ANALYSIS")
    print("=" * 65)

    print(
        "Relevant schemes missed from Top-10:",
        len(missed_df)
    )

    print(
        "Queries with irrelevant Rank-1 result:",
        irrelevant_rank1["query_id"].nunique()
    )

    print(
        "Relevant results at Rank 9 or 10:",
        len(low_rank_relevant)
    )

    print(
        "Ambiguous/underspecified queries:",
        ambiguous_queries["query_id"].nunique()
    )

    print("=" * 65)

    print("\nFiles created:")

    print(
        "1.",
        f"{OUTPUT_DIR}/error_missed_relevant.csv"
    )

    print(
        "2.",
        f"{OUTPUT_DIR}/error_irrelevant_rank1.csv"
    )

    print(
        "3.",
        f"{OUTPUT_DIR}/error_relevant_rank9_10.csv"
    )

    print(
        "4.",
        f"{OUTPUT_DIR}/error_ambiguous_queries.csv"
    )

    print("=" * 65)


if __name__ == "__main__":
    main()