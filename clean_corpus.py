import pandas as pd
import os
import re

# ============================================================
# Day 3 - Clean Corpus and Build Retrieval Corpus
# Designed for:
# data/raw/schemes.csv
# ============================================================

RAW_FILE = "data/raw/schemes.csv"
PROCESSED_FOLDER = "data/processed"

CLEAN_FILE = os.path.join(
    PROCESSED_FOLDER,
    "schemes_clean.csv"
)

RETRIEVAL_FILE = os.path.join(
    PROCESSED_FOLDER,
    "retrieval_corpus.csv"
)


# ------------------------------------------------------------
# 1. Create processed folder
# ------------------------------------------------------------

os.makedirs(PROCESSED_FOLDER, exist_ok=True)


# ------------------------------------------------------------
# 2. Read the CSV
# ------------------------------------------------------------
# Your current CSV uses these columns:
#
# ID, Scholarship, Ministry, Category, Status,
# Target_group, Description, Eligibility, Benefits,
# Required_documents, Application_mode, Keywords,
# Official_url, Source, Verification_date, Rule_version
#
# The encoding fallback is included because the supplied CSV
# contains characters that are not valid UTF-8.

def read_csv_safely(path):
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin1"]

    for encoding in encodings:
        try:
            df = pd.read_csv(path, encoding=encoding)
            print(f"CSV loaded using encoding: {encoding}")
            return df
        except UnicodeDecodeError:
            continue

    raise ValueError("Could not decode the CSV using the supported encodings.")


df = read_csv_safely(RAW_FILE)

print("\nRaw dataset loaded successfully.")
print("Total schemes:", len(df))


# ------------------------------------------------------------
# 3. Clean column names
# ------------------------------------------------------------

df.columns = df.columns.str.strip()


# ------------------------------------------------------------
# 4. Check the columns that exist in YOUR CSV
# ------------------------------------------------------------

required_columns = [
    "ID",
    "Scholarship",
    "Ministry",
    "Category",
    "Status",
    "Target_group",
    "Description",
    "Eligibility",
    "Benefits",
    "Required_documents",
    "Application_mode",
    "Keywords",
    "Official_url",
    "Source",
    "Verification_date",
    "Rule_version"
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    print("\nERROR: These columns are missing:")
    for column in missing_columns:
        print("-", column)

    raise ValueError("Your CSV does not match the expected Day 3 schema.")


# ------------------------------------------------------------
# 5. Clean text values
# ------------------------------------------------------------

def clean_text(value):
    if pd.isna(value):
        return ""

    value = str(value)

    # Replace line breaks/tabs/multiple spaces with one space
    value = re.sub(r"\s+", " ", value)

    return value.strip()


for column in df.columns:
    df[column] = df[column].apply(clean_text)


# ------------------------------------------------------------
# 6. Check duplicate scheme IDs
# ------------------------------------------------------------

duplicate_ids = df[df["ID"].duplicated(keep=False)]

if len(duplicate_ids) > 0:
    print("\nWARNING: Duplicate scheme IDs found:")
    print(duplicate_ids["ID"].tolist())
else:
    print("All scheme IDs are unique.")


# ------------------------------------------------------------
# 7. Check missing important values
# ------------------------------------------------------------

important_columns = [
    "ID",
    "Scholarship",
    "Category",
    "Target_group",
    "Description",
    "Eligibility",
    "Benefits",
    "Keywords",
    "Official_url",
    "Source",
    "Rule_version"
]

print("\nMissing/empty values:")
for column in important_columns:
    empty_count = (df[column].str.strip() == "").sum()
    print(f"{column}: {empty_count}")


# ------------------------------------------------------------
# 8. Save cleaned dataset
# ------------------------------------------------------------
# IMPORTANT:
# data/raw/schemes.csv is NEVER modified.

df.to_csv(
    CLEAN_FILE,
    index=False,
    encoding="utf-8-sig"
)

print("\nClean dataset saved to:")
print(CLEAN_FILE)


# ------------------------------------------------------------
# 9. Build retrieval text
# ------------------------------------------------------------
#
# The supplied CSV does NOT contain a Study_level column.
# Therefore, this script does NOT invent one.
#
# Retrieval text uses the fields actually present in your CSV
# that are relevant to scholarship search:
#
# Scholarship
# Category
# Target_group
# Description
# Eligibility
# Benefits
# Keywords
#
# Ministry, status, documents, application mode, URL, source,
# verification date and rule version remain outside retrieval
# text as metadata/supporting information.

def build_retrieval_text(row):

    return (
        f"Scheme Name: {row['Scholarship']}. "
        f"Category: {row['Category']}. "
        f"Target Group: {row['Target_group']}. "
        f"Description: {row['Description']}. "
        f"Eligibility: {row['Eligibility']}. "
        f"Benefits: {row['Benefits']}. "
        f"Keywords: {row['Keywords']}."
    )


df["retrieval_text"] = df.apply(
    build_retrieval_text,
    axis=1
)


# ------------------------------------------------------------
# 10. Create retrieval corpus
# ------------------------------------------------------------

retrieval_df = pd.DataFrame({
    "scheme_id": df["ID"],
    "scheme_name": df["Scholarship"],
    "retrieval_text": df["retrieval_text"],
    "official_url": df["Official_url"],
    "source_name": df["Source"],
    "rule_version": df["Rule_version"]
})


# ------------------------------------------------------------
# 11. Check empty retrieval text
# ------------------------------------------------------------

empty_retrieval = retrieval_df[
    retrieval_df["retrieval_text"].str.strip() == ""
]

print("\nEmpty retrieval texts:", len(empty_retrieval))


# ------------------------------------------------------------
# 12. Check duplicate retrieval text
# ------------------------------------------------------------

duplicate_retrieval = retrieval_df[
    retrieval_df["retrieval_text"].duplicated(keep=False)
]

print("Duplicate retrieval texts:", len(duplicate_retrieval))

if len(duplicate_retrieval) > 0:
    print("\nWARNING: Duplicate retrieval text found for:")
    print(
        duplicate_retrieval[
            ["scheme_id", "scheme_name"]
        ].to_string(index=False)
    )


# ------------------------------------------------------------
# 13. Save retrieval corpus
# ------------------------------------------------------------

retrieval_df.to_csv(
    RETRIEVAL_FILE,
    index=False,
    encoding="utf-8-sig"
)

print("\nRetrieval corpus saved to:")
print(RETRIEVAL_FILE)


# ------------------------------------------------------------
# 14. Final validation
# ------------------------------------------------------------

print("\n==============================")
print("DAY 3 VALIDATION")
print("==============================")

print("Raw corpus count:       ", len(df))
print("Clean corpus count:     ", len(df))
print("Retrieval corpus count: ", len(retrieval_df))

print(
    "Empty retrieval texts:  ",
    len(empty_retrieval)
)

print(
    "Duplicate retrieval text:",
    len(duplicate_retrieval)
)

print("\nRetrieval corpus columns:")
print(retrieval_df.columns.tolist())


# ------------------------------------------------------------
# 15. Check that corpus size was preserved
# ------------------------------------------------------------

if len(df) != len(retrieval_df):
    raise ValueError(
        "ERROR: The number of schemes changed while creating "
        "the retrieval corpus."
    )

print("\nCorpus size preserved successfully.")


# ------------------------------------------------------------
# 16. Final message
# ------------------------------------------------------------

print("\nDay 3 corpus preparation completed successfully.")

print("\nCreated files:")
print("1.", CLEAN_FILE)
print("2.", RETRIEVAL_FILE)

print("\nIMPORTANT:")
print("The original file was not modified:")
print(RAW_FILE)