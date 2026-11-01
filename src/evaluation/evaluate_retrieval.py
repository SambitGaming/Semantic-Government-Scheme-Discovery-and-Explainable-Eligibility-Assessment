from pathlib import Path
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path("data/benchmark")
OUT = Path("results")
MODELS = ["bm25", "minilm", "mpnet"]
K_VALUES = [5, 10]
RNG = np.random.default_rng(42)


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)


def find_column(df, candidates, description):
    for name in candidates:
        if name in df.columns:
            return name

    raise ValueError(
        f"Cannot find {description}. "
        f"Available columns: {df.columns.tolist()}"
    )


def normalize_ids(df):
    """
    Normalize query_id and scheme_id so that values such as
    'Q001' and ' Q001 ' are treated as the same ID.
    """
    df["query_id"] = (
        df["query_id"]
        .astype(str)
        .str.strip()
    )

    df["scheme_id"] = (
        df["scheme_id"]
        .astype(str)
        .str.strip()
    )

    return df


def prepare_one_judgment_file(path):
    """
    Read one relevance judgment CSV and convert it into the
    standard format:

    query_id
    scheme_id
    relevance
    """

    df = read_csv(path)

    qcol = find_column(
        df,
        ["query_id"],
        "query ID"
    )

    scol = find_column(
        df,
        ["scheme_id", "candidate_id"],
        "scheme ID"
    )

    # IMPORTANT:
    # Prefer relevance_label over relevance_score.
    #
    # Your previous error happened because the CSV contained
    # the actual label in one column while the evaluation code
    # was reading another empty column.
    rcol = find_column(
        df,
        [
            "relevance_label",
            "relevance",
            "relevance_score",
            "relevance_judgments"
        ],
        "graded relevance label"
    )

    df = df.rename(columns={
        qcol: "query_id",
        scol: "scheme_id",
        rcol: "relevance"
    })

    df = normalize_ids(df)

    # Convert text relevance labels into numerical grades.
    label_map = {
        "relevant": 2,
        "partially relevant": 1,
        "not relevant": 0,
        "not_relevant": 0,
        "partially_relevant": 1,
        "2": 2,
        "1": 1,
        "0": 0,
    }

    # Convert to string first so both text and numeric values
    # can be handled consistently.
    df["relevance"] = (
        df["relevance"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(label_map)
    )

    df["relevance"] = pd.to_numeric(
        df["relevance"],
        errors="coerce"
    )

    # Check for missing/invalid labels.
    if df["relevance"].isna().any():

        bad = df.loc[
            df["relevance"].isna()
        ].head(20)

        raise ValueError(
            f"Unrecognized or missing relevance labels in "
            f"{path}. Inspect these rows:\n"
            + bad.to_string(index=False)
        )

    # Only 0, 1 and 2 are allowed.
    if not df["relevance"].isin([0, 1, 2]).all():
        raise ValueError(
            f"Invalid relevance score found in {path}. "
            "Allowed values are 0, 1 and 2."
        )

    return df[
        ["query_id", "scheme_id", "relevance"]
    ]


def prepare_judgments():
    """
    Load BOTH judgment files.

    This fixes the Q001 problem where C001 and C019 were
    present in relevance_judgments.csv but absent from
    additional_relevance_judgments.csv.
    """

    original_path = BASE / "relevance_judgments.csv"
    additional_path = BASE / "additional_relevance_judgments.csv"

    frames = []

    if original_path.exists():
        print(
            f"Loading original judgments: {original_path}"
        )

        frames.append(
            prepare_one_judgment_file(
                original_path
            )
        )

    if additional_path.exists():
        print(
            f"Loading additional judgments: "
            f"{additional_path}"
        )

        frames.append(
            prepare_one_judgment_file(
                additional_path
            )
        )

    if not frames:
        raise FileNotFoundError(
            "No relevance judgment files were found. "
            "Expected at least one of:\n"
            f"  {original_path}\n"
            f"  {additional_path}"
        )

    # Combine both files.
    df = pd.concat(
        frames,
        ignore_index=True
    )

    df = normalize_ids(df)

    # Check for conflicting judgments.
    #
    # Example:
    # Q001/C001 = 2 in one file
    # Q001/C001 = 0 in another file
    #
    # That must not silently pass.
    conflict_counts = (
        df.groupby(
            ["query_id", "scheme_id"]
        )["relevance"]
        .nunique()
    )

    conflicts = conflict_counts[
        conflict_counts > 1
    ]

    if not conflicts.empty:

        conflict_rows = df[
            df.set_index(
                ["query_id", "scheme_id"]
            ).index.isin(
                conflicts.index
            )
        ]

        raise ValueError(
            "Conflicting relevance judgments found:\n"
            + conflict_rows.to_string(index=False)
        )

    # Remove exact duplicate judgments.
    df = df.drop_duplicates(
        subset=["query_id", "scheme_id"],
        keep="last"
    )

    print(
        f"Loaded {len(df)} unique relevance judgments."
    )

    return df[
        ["query_id", "scheme_id", "relevance"]
    ]


def prepare_results(model):

    path = BASE / f"{model}_results.csv"

    df = read_csv(path)

    qcol = find_column(
        df,
        ["query_id"],
        "query ID"
    )

    scol = find_column(
        df,
        ["scheme_id", "candidate_id"],
        "scheme ID"
    )

    rcol = find_column(
        df,
        ["rank"],
        "retrieval rank"
    )

    df = df.rename(columns={
        qcol: "query_id",
        scol: "scheme_id",
        rcol: "rank"
    })

    # Normalize IDs.
    df = normalize_ids(df)

    df["rank"] = pd.to_numeric(
        df["rank"],
        errors="raise"
    )

    df = df.sort_values(
        ["query_id", "rank"]
    )

    if df.duplicated(
        ["query_id", "rank"]
    ).any():

        duplicates = df[
            df.duplicated(
                ["query_id", "rank"],
                keep=False
            )
        ]

        raise ValueError(
            f"{model}: duplicate query/rank pairs found:\n"
            + duplicates.to_string(index=False)
        )

    return df


def dcg(grades, k):

    grades = np.asarray(
        grades[:k],
        dtype=float
    )

    if len(grades) == 0:
        return 0.0

    gains = np.power(
        2.0,
        grades
    ) - 1.0

    discounts = np.log2(
        np.arange(
            2,
            len(grades) + 2
        )
    )

    return float(
        np.sum(
            gains / discounts
        )
    )


def evaluate_query(group, judgment_map):

    group = group.sort_values("rank")

    qid = str(
        group["query_id"].iloc[0]
    ).strip()

    # Normalize scheme IDs.
    scheme_ids = [
        str(sid).strip()
        for sid in group["scheme_id"]
    ]

    # Find missing judgments.
    missing = [
        sid
        for sid in scheme_ids
        if (qid, sid) not in judgment_map
    ]

    if missing:

        raise ValueError(
            f"{qid}: {len(missing)} retrieved schemes "
            f"have no judgment: {missing}\n\n"
            "Complete the judgments or check that both "
            "relevance_judgments.csv and "
            "additional_relevance_judgments.csv are "
            "being loaded."
        )

    grades = [
        judgment_map[
            (qid, sid)
        ]
        for sid in scheme_ids
    ]

    binary = [
        int(g >= 1)
        for g in grades
    ]

    total_relevant = sum(
        1
        for (query, _),
        grade in judgment_map.items()
        if query == qid and grade >= 1
    )

    row = {
        "query_id": qid
    }

    for k in K_VALUES:

        top_grades = grades[:k]

        top_binary = binary[:k]

        row[
            f"Precision@{k}"
        ] = (
            sum(top_binary) / k
        )

        row[
            f"Recall@{k}"
        ] = (
            sum(top_binary) / total_relevant
            if total_relevant
            else np.nan
        )

        ideal = sorted(
            [
                grade
                for (query, _),
                grade in judgment_map.items()
                if query == qid
            ],
            reverse=True
        )

        ideal_dcg = dcg(
            ideal,
            k
        )

        row[
            f"nDCG@{k}"
        ] = (
            dcg(
                top_grades,
                k
            ) / ideal_dcg
            if ideal_dcg
            else np.nan
        )

    first_relevant_rank = next(
        (
            int(rank)
            for rank, rel in zip(
                group["rank"],
                binary
            )
            if rel == 1
        ),
        None
    )

    row["MRR"] = (
        1.0 / first_relevant_rank
        if first_relevant_rank is not None
        else 0.0
    )

    return row


def main():

    OUT.mkdir(
        exist_ok=True
    )

    print(
        "\n========================================"
    )
    print(
        "Preparing relevance judgments..."
    )
    print(
        "========================================"
    )

    judgments = prepare_judgments()

    judgment_map = {
        (
            str(row.query_id).strip(),
            str(row.scheme_id).strip()
        ): int(row.relevance)

        for row in judgments.itertuples(
            index=False
        )
    }

    print(
        f"Judgment map contains "
        f"{len(judgment_map)} entries."
    )

    query_df = read_csv(
        BASE / "queries.csv"
    )

    if "query_id" not in query_df.columns:
        raise ValueError(
            "queries.csv needs query_id."
        )

    query_df["query_id"] = (
        query_df["query_id"]
        .astype(str)
        .str.strip()
    )

    all_per_query = {}
    all_results = {}

    for model in MODELS:

        print(
            f"\nEvaluating {model.upper()}..."
        )

        results = prepare_results(
            model
        )

        result_query_ids = set(
            results["query_id"]
        )

        benchmark_query_ids = set(
            query_df["query_id"]
        )

        if (
            result_query_ids
            != benchmark_query_ids
        ):

            missing_queries = (
                benchmark_query_ids
                - result_query_ids
            )

            extra_queries = (
                result_query_ids
                - benchmark_query_ids
            )

            raise ValueError(
                f"{model}: result query IDs do not "
                "match queries.csv.\n"
                f"Missing queries: {missing_queries}\n"
                f"Extra queries: {extra_queries}"
            )

        evaluated = []

        for qid, group in results.groupby(
            "query_id"
        ):

            evaluated.append(
                evaluate_query(
                    group,
                    judgment_map
                )
            )

        per_query = pd.DataFrame(
            evaluated
        )

        all_per_query[
            model
        ] = per_query

        all_results[
            model
        ] = results

        model_dir = (
            OUT / model
        )

        model_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        per_query.to_csv(
            model_dir /
            f"{model}_per_query.csv",
            index=False
        )

        metrics = [
            "Precision@5",
            "Recall@5",
            "Precision@10",
            "Recall@10",
            "MRR",
            "nDCG@5",
            "nDCG@10"
        ]

        summary = pd.DataFrame({
            "metric": metrics,
            "value": [
                per_query[m].mean()
                for m in metrics
            ]
        })

        summary.to_csv(
            model_dir /
            f"{model}_metrics.csv",
            index=False
        )

        print(
            f"\n{model.upper()} metrics"
        )

        print(
            summary.to_string(
                index=False
            )
        )

    # ----------------------------------------
    # Overall comparison
    # ----------------------------------------

    metric_names = [
        "Precision@5",
        "Recall@5",
        "Precision@10",
        "Recall@10",
        "MRR",
        "nDCG@5",
        "nDCG@10"
    ]

    comparison = pd.DataFrame({
        "Metric": metric_names
    })

    for model in MODELS:

        comparison[
            model.upper()
        ] = [
            all_per_query[
                model
            ][metric].mean()
            for metric in metric_names
        ]

    comparison.to_csv(
        OUT /
        "retrieval_comparison.csv",
        index=False
    )

    # ----------------------------------------
    # Per-query comparison
    # ----------------------------------------

    merged = None

    for model in MODELS:

        cols = (
            all_per_query[model][
                [
                    "query_id",
                    "MRR",
                    "nDCG@10",
                    "Precision@10"
                ]
            ]
            .rename(columns={
                "MRR":
                    f"{model.upper()}_MRR",

                "nDCG@10":
                    f"{model.upper()}_nDCG@10",

                "Precision@10":
                    f"{model.upper()}_Precision@10"
            })
        )

        merged = (
            cols
            if merged is None
            else merged.merge(
                cols,
                on="query_id",
                how="inner"
            )
        )

    merged.to_csv(
        OUT /
        "per_query_comparison.csv",
        index=False
    )

    # ----------------------------------------
    # Query type comparison
    # ----------------------------------------

    type_col = next(
        (
            c
            for c in [
                "query_type",
                "query_category",
                "category"
            ]
            if c in query_df.columns
        ),
        None
    )

    if type_col:

        grouped = merged.merge(
            query_df[
                [
                    "query_id",
                    type_col
                ]
            ],
            on="query_id"
        )

        type_metrics = [
            c
            for c in grouped.columns
            if (
                "nDCG@10" in c
                or c.endswith("_MRR")
            )
        ]

        (
            grouped
            .groupby(type_col)[
                type_metrics
            ]
            .mean()
            .reset_index()
            .to_csv(
                OUT /
                "query_type_comparison.csv",
                index=False
            )
        )

    # ----------------------------------------
    # Top-1 error inspection
    # ----------------------------------------

    top1 = {}

    for model in MODELS:

        top1[model] = (
            all_results[model]
            .sort_values("rank")
            .groupby("query_id")
            .first()["scheme_id"]
            .rename(
                f"{model.upper()}_top1"
            )
        )

    errors = pd.concat(
        top1.values(),
        axis=1
    ).reset_index()

    errors = errors.merge(
        query_df,
        on="query_id",
        how="left"
    )

    errors.to_csv(
        OUT /
        "error_analysis.csv",
        index=False
    )

    # ----------------------------------------
    # Hard-negative and ambiguous subsets
    # ----------------------------------------

    if type_col:

        labels = (
            query_df[type_col]
            .astype(str)
            .str.lower()
        )

        for name, keywords in {
            "hard_negative_analysis":
                [
                    "hard_negative",
                    "hard negative"
                ],

            "ambiguous_query_analysis":
                [
                    "ambiguous"
                ]

        }.items():

            mask = labels.apply(
                lambda value:
                any(
                    word in value
                    for word in keywords
                )
            )

            subset_ids = set(
                query_df.loc[
                    mask,
                    "query_id"
                ]
            )

            errors[
                errors["query_id"].isin(
                    subset_ids
                )
            ].to_csv(
                OUT / f"{name}.csv",
                index=False
            )

    # ----------------------------------------
    # Metric charts
    # ----------------------------------------

    chart_metrics = [
        "Precision@5",
        "Recall@10",
        "MRR",
        "nDCG@10"
    ]

    for metric in chart_metrics:

        values = [
            all_per_query[m][
                metric
            ].mean()
            for m in MODELS
        ]

        plt.figure()

        plt.bar(
            [
                "BM25",
                "MiniLM",
                "MPNet"
            ],
            values
        )

        plt.ylabel(metric)

        plt.title(
            f"Retrieval comparison: {metric}"
        )

        plt.tight_layout()

        plt.savefig(
            OUT /
            f"{metric.replace('@', '_at_')}.png"
        )

        plt.close()

    print(
        "\n========================================"
    )
    print(
        "Evaluation completed successfully."
    )
    print(
        "========================================"
    )

    print(
        "\nCreated:"
    )

    print(
        "results/retrieval_comparison.csv"
    )

    print(
        "results/per_query_comparison.csv"
    )

    print(
        "results/error_analysis.csv"
    )

    print(
        "results/<model>/<model>_metrics.csv"
    )

    print(
        "results/<model>/<model>_per_query.csv"
    )

    print(
        "results/*.png"
    )


if __name__ == "__main__":
    main()