import pandas as pd
from pathlib import Path

INPUT_FILE = "data/raw/schemes.csv"
OUTPUT_FILE = "data/processed/bm25_corpus.csv"

# Read CSV using Windows encoding
df = pd.read_csv(INPUT_FILE, encoding="cp1252")

def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()

documents = []

for _, row in df.iterrows():

    document = " ".join([
        clean_text(row.get("Scholarship")),
        clean_text(row.get("Description")),
        clean_text(row.get("Benefits")),
        clean_text(row.get("Eligibility")),
        clean_text(row.get("Category")),
        clean_text(row.get("Keywords"))
    ])

    documents.append({
        "document_id": f"DOC_{row['ID']}",
        "scheme_id": row["ID"],
        "scheme_name": row["Scholarship"],
        "bm25_document": document
    })

output_df = pd.DataFrame(documents)

Path("data/processed").mkdir(parents=True, exist_ok=True)

output_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)

print("BM25 corpus created successfully!")
print("Documents:", len(output_df))
print("Saved to:", OUTPUT_FILE)