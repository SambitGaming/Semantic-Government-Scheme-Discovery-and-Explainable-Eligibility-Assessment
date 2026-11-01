import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/government_schemes.db")
CSV_PATH = Path("data/processed/schemes_clean.csv")

# Load CSV
df = pd.read_csv(CSV_PATH, dtype=str).fillna("")

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

updated = 0
inserted = 0

for _, row in df.iterrows():

    scheme_id = str(row["ID"]).strip()

    # Check whether scheme already exists
    existing = cursor.execute(
        "SELECT scheme_id FROM schemes WHERE scheme_id = ?",
        (scheme_id,)
    ).fetchone()

    values = (
        scheme_id,
        row["Scholarship"].strip(),
        row["Ministry"].strip(),
        row["Category"].strip(),
        row["Status"].strip(),
        row["Target_group"].strip(),
        row["Description"].strip(),
        row["Eligibility"].strip(),
        row["Benefits"].strip(),
        row["Required_documents"].strip(),
        row["Application_mode"].strip(),
        row["Keywords"].strip(),
        row["Official_url"].strip(),
        row["Source"].strip(),
        row["Verification_date"].strip(),
        row["Rule_version"].strip()
    )

    if existing:
        cursor.execute(
            """
            UPDATE schemes
            SET
                scheme_name = ?,
                ministry = ?,
                category = ?,
                status = ?,
                target_group = ?,
                description = ?,
                eligibility = ?,
                benefits = ?,
                required_documents = ?,
                application_mode = ?,
                keywords = ?,
                Official_url = ?,
                source = ?,
                verification_date = ?,
                rule_version = ?
            WHERE scheme_id = ?
            """,
            (
                values[1],
                values[2],
                values[3],
                values[4],
                values[5],
                values[6],
                values[7],
                values[8],
                values[9],
                values[10],
                values[11],
                values[12],
                values[13],
                values[14],
                values[15],
                scheme_id
            )
        )

        updated += 1

    else:
        cursor.execute(
            """
            INSERT INTO schemes (
                scheme_id,
                scheme_name,
                ministry,
                category,
                status,
                target_group,
                description,
                eligibility,
                benefits,
                required_documents,
                application_mode,
                keywords,
                Official_url,
                source,
                verification_date,
                rule_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values
        )

        inserted += 1

conn.commit()
conn.close()

print("Synchronization completed.")
print("Existing schemes updated:", updated)
print("New schemes inserted:", inserted)
print("Total CSV records:", len(df))