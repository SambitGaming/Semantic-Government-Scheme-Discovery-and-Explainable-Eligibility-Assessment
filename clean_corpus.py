
import pandas as pd
import os
import re

# -----------------------------------
# 1. File paths
# -----------------------------------

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

# -----------------------------------
# 2. Create processed folder
# -----------------------------------

os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# -----------------------------------
# 3. Read raw CSV
# -----------------------------------

df = pd.read_csv(RAW_FILE, encoding="cp1252")

print("Raw dataset loaded")
print("Total schemes:", len(df))

# -----------------------------------
# 4. Clean column names
# -----------------------------------

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# -----------------------------------
# 5. Clean text values
# -----------------------------------

def clean_text(value):
    if pd.isna(value):
        return ""

    value = str(value)

    # Remove unnecessary spaces
    value = re.sub(r"\s+", " ", value)

    return value.strip()


# Clean every column
for column in df.columns:
    df[column] = df[column].apply(clean_text)

# -----------------------------------
# 6. Check required columns
# -----------------------------------

required_columns = [
    "scheme_id",
    "scheme_name",
    "category",
    "study_level",
    "target_group",
    "description",
    "eligibility",
    "benefits",
    "keywords",
    "official_url",
    "source_name",
    "rule_version"
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    print("Missing columns:", missing_columns)
    raise ValueError("Required columns are missing.")

# -----------------------------------
# 7. Check duplicate IDs
# -----------------------------------

duplicate_ids = df[
    df["scheme_id"].duplicated(keep=False)
]

if len(duplicate_ids) > 0:
    print("WARNING: Duplicate scheme IDs found")
    print(duplicate_ids["scheme_id"].tolist())
else:
    print("All scheme IDs are unique")

# -----------------------------------
# 8. Save cleaned dataset
# -----------------------------------

df.to_csv(CLEAN_FILE, index=False)

print("Clean dataset saved:", CLEAN_FILE)

# -----------------------------------
# 9. Build retrieval text
# -----------------------------------

def build_retrieval_text(row):

    return (
        f"Scheme Name: {row['scheme_name']}. "
        f"Category: {row['category']}. "
        f"Study Level: {row['study_level']}. "
        f"Target Group: {row['target_group']}. "
        f"Description: {row['description']}. "
        f"Eligibility: {row['eligibility']}. "
        f"Benefits: {row['benefits']}. "
        f"Keywords: {row['keywords']}."
    )


df["retrieval_text"] = df.apply(
    build_retrieval_text,
    axis=1
)

# -----------------------------------
# 10. Create retrieval corpus
# -----------------------------------

retrieval_columns = [
    "scheme_id",
    "scheme_name",
    "retrieval_text",
    "official_url",
    "source_name",
    "rule_version"
]

retrieval_df = df[retrieval_columns].copy()

retrieval_df.to_csv(
    RETRIEVAL_FILE,
    index=False
)

print("Retrieval corpus saved:", RETRIEVAL_FILE)

# -----------------------------------
# 11. Validation
# -----------------------------------

print("\n--- VALIDATION ---")

print("Raw schemes:", len(df))
print("Clean schemes:", len(df))
print("Retrieval schemes:", len(retrieval_df))

# Check empty retrieval text
empty_text = retrieval_df[
    retrieval_df["retrieval_text"].str.strip() == ""
]

print("Empty retrieval texts:", len(empty_text))

# Check duplicate retrieval text
duplicate_text = retrieval_df[
    retrieval_df["retrieval_text"].duplicated(keep=False)
]

print("Duplicate retrieval texts:", len(duplicate_text))

# Check missing metadata
print("\nMissing values:")
print(retrieval_df.isnull().sum())

print("\nDay 3 corpus preparation complete!")