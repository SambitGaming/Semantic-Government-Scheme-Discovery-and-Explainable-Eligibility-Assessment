from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "retrieval_corpus.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "semantic_corpus.csv"
)


def clean_value(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def find_column(df, possible_names):
    for name in possible_names:
        if name in df.columns:
            return name

    return None


def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print("Input columns:")
    print(df.columns.tolist())

    scheme_id_column = find_column(
        df,
        [
            "scheme_id",
            "Scheme_ID",
            "ID",
            "Id"
        ]
    )

    scheme_name_column = find_column(
        df,
        [
            "scheme_name",
            "Scholarship",
            "Scheme_Name",
            "name"
        ]
    )

    if scheme_id_column is None:
        raise ValueError(
            "Could not find scheme ID column."
        )

    if scheme_name_column is None:
        raise ValueError(
            "Could not find scheme name column."
        )

    # Columns that should NOT be embedded
    excluded_columns = {
        scheme_id_column,
        "official_url",
        "Official_url",
        "source",
        "Source",
        "verification_date",
        "Verification_date"
    }

    text_columns = [
        column
        for column in df.columns
        if column not in excluded_columns
    ]

    corpus = pd.DataFrame()

    corpus["scheme_id"] = (
        df[scheme_id_column]
        .fillna("")
        .astype(str)
    )

    corpus["scheme_name"] = (
        df[scheme_name_column]
        .fillna("")
        .astype(str)
    )

    # Keep useful display fields when available
    description_column = find_column(
        df,
        [
            "description",
            "Description"
        ]
    )

    category_column = find_column(
        df,
        [
            "category",
            "Category"
        ]
    )

    official_url_column = find_column(
        df,
        [
            "official_url",
            "Official_url"
        ]
    )

    if description_column:
        corpus["description"] = (
            df[description_column]
            .fillna("")
            .astype(str)
        )
    else:
        corpus["description"] = ""

    if category_column:
        corpus["category"] = (
            df[category_column]
            .fillna("")
            .astype(str)
        )
    else:
        corpus["category"] = ""

    if official_url_column:
        corpus["official_url"] = (
            df[official_url_column]
            .fillna("")
            .astype(str)
        )
    else:
        corpus["official_url"] = ""

    # Create text for semantic embedding
    corpus["search_text"] = df.apply(
        lambda row: " ".join(
            f"{column}: {clean_value(row[column])}"
            for column in text_columns
            if clean_value(row[column])
        ),
        axis=1
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    corpus.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("Semantic corpus created successfully.")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Number of schemes: {len(corpus)}")
    print()
    print("Output columns:")
    print(corpus.columns.tolist())


if __name__ == "__main__":
    main()