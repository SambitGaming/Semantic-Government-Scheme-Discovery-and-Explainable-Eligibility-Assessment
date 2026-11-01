
from pathlib import Path
import re
import pandas as pd

# --------------------------------------------------
# FIND PROJECT ROOT AUTOMATICALLY
# --------------------------------------------------

CURRENT_DIR = Path(__file__).resolve().parent

def find_project_root(start_dir):
    """Find the folder containing data/benchmark and data/processed."""

    for folder in [start_dir, *start_dir.parents]:
        if (
            (folder / "data" / "benchmark").is_dir()
            and (folder / "data" / "processed").is_dir()
        ):
            return folder

    raise FileNotFoundError(
        "Could not find the project root. Make sure this script is "
        "inside your project folder."
    )


ROOT = find_project_root(CURRENT_DIR)

MISSING_FILE = ROOT / "data" / "benchmark" / "missing_judgments_to_review.csv"
QUERIES_FILE = ROOT / "data" / "benchmark" / "queries.csv"
SCHEMES_FILE = ROOT / "data" / "processed" / "schemes_clean.csv"
OUTPUT_FILE = ROOT / "data" / "benchmark" / "missing_judgments_suggested.csv"

# --------------------------------------------------
# KEYWORD SETTINGS
# --------------------------------------------------

STOPWORDS = {
    "a", "an", "the", "is", "am", "are", "was", "were",
    "i", "me", "my", "we", "you", "he", "she", "they",
    "and", "or", "but", "for", "to", "of", "in", "on",
    "at", "by", "with", "from", "as", "it", "this", "that",
    "can", "could", "want", "need", "please", "help", "find",
    "get", "apply", "application", "available", "government",
    "india", "scheme", "schemes", "scholarship", "scholarships",
    "student", "students", "education", "educational", "higher",
    "study", "studies", "who", "what", "which", "how"
}

TEXT_COLUMNS = [
    "Scholarship",
    "Ministry",
    "Category",
    "Target_group",
    "Description",
    "Eligibility",
    "Benefits",
    "Required_documents",
    "Application_mode",
    "Keywords"
]


def normalize_id(value):
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def tokenize(value):
    if pd.isna(value):
        return set()

    words = re.findall(r"[a-zA-Z0-9]+", str(value).lower())

    return {
        word for word in words
        if len(word) >= 3 and word not in STOPWORDS
    }


def classify_query(query_text, scheme_text):
    query_terms = tokenize(query_text)
    scheme_terms = tokenize(scheme_text)
    matched_terms = sorted(query_terms & scheme_terms)

    if not query_terms:
        return {
            "suggested_label": "Needs Review",
            "suggested_score": "",
            "matched_terms": "",
            "keyword_overlap": 0.0,
            "confidence": "Low",
            "suggestion_reason": "No informative query terms found."
        }

    overlap = len(matched_terms) / len(query_terms)

    if len(matched_terms) >= 2 and overlap >= 0.35:
        label = "Relevant"
        score = 2
        confidence = "Medium" if overlap < 0.60 else "High"
        reason = "Multiple informative query terms match the scheme."

    elif matched_terms:
        label = "Partially Relevant"
        score = 1
        confidence = "Low" if overlap < 0.20 else "Medium"
        reason = "Some query terms match; contextual verification is needed."

    else:
        label = "Needs Review"
        score = ""
        confidence = "Low"
        reason = (
            "No keyword overlap found. This does not prove irrelevance; "
            "check semantic meaning before assigning a final label."
        )

    return {
        "suggested_label": label,
        "suggested_score": score,
        "matched_terms": "; ".join(matched_terms),
        "keyword_overlap": round(overlap, 3),
        "confidence": confidence,
        "suggestion_reason": reason
    }


def main():
    print("Project root:", ROOT)

    # Check required input files
    for file_path in [MISSING_FILE, QUERIES_FILE, SCHEMES_FILE]:
        if not file_path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}\n"
                "Check that the file exists in your project."
            )

    missing = pd.read_csv(MISSING_FILE, dtype=str).fillna("")
    queries = pd.read_csv(QUERIES_FILE, dtype=str).fillna("")
    schemes = pd.read_csv(SCHEMES_FILE, dtype=str).fillna("")

    # Check required columns
    if not {"query_id", "scheme_id"}.issubset(missing.columns):
        raise ValueError(
            f"Unexpected columns in missing-judgments file: "
            f"{list(missing.columns)}"
        )

    if not {"query_id", "query_text"}.issubset(queries.columns):
        raise ValueError("queries.csv needs query_id and query_text.")

    if not {"ID", "Scholarship"}.issubset(schemes.columns):
        raise ValueError("schemes_clean.csv needs ID and Scholarship.")

    # Normalize IDs
    missing["query_key"] = missing["query_id"].map(normalize_id)
    missing["scheme_key"] = missing["scheme_id"].map(normalize_id)
    queries["query_key"] = queries["query_id"].map(normalize_id)
    schemes["scheme_key"] = schemes["ID"].map(normalize_id)

    # Query lookup
    query_lookup = (
        queries.drop_duplicates("query_key")
        .set_index("query_key")["query_text"]
        .to_dict()
    )

    # Scheme lookup
    available_columns = [
        column for column in TEXT_COLUMNS
        if column in schemes.columns
    ]

    schemes["scheme_text"] = schemes[available_columns].agg(
        " ".join, axis=1
    )

    scheme_lookup = (
        schemes.drop_duplicates("scheme_key")
        .set_index("scheme_key")["scheme_text"]
        .to_dict()
    )

    # Generate suggestions
    suggestions = []

    for _, row in missing.iterrows():
        query_text = query_lookup.get(row["query_key"])
        scheme_text = scheme_lookup.get(row["scheme_key"])

        if query_text is None or scheme_text is None:
            result = {
                "suggested_label": "Needs Review",
                "suggested_score": "",
                "matched_terms": "",
                "keyword_overlap": "",
                "confidence": "Low",
                "suggestion_reason": (
                    "Query ID or scheme ID could not be matched."
                )
            }
        else:
            result = classify_query(query_text, scheme_text)

        suggestions.append(result)

    # Combine original rows with suggestions
    output = missing.drop(
        columns=["query_key", "scheme_key"], errors="ignore"
    ).copy()

    suggestions_df = pd.DataFrame(suggestions, index=output.index)

    output = pd.concat([output, suggestions_df], axis=1)
    output["review_status"] = "Pending Review"

    # Save without modifying the original judgments
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("\nSuggestions generated successfully.")
    print("Input pairs:", len(missing))
    print("Output file:", OUTPUT_FILE)

    print("\nSuggested label counts:")
    print(output["suggested_label"].value_counts(dropna=False))

    print("\nConfidence counts:")
    print(output["confidence"].value_counts(dropna=False))

    print("\nAll suggestions are provisional.")
    print("Original relevance_judgments.csv was not modified.")


if __name__ == "__main__":
    main()