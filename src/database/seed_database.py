import pandas as pd

from database import get_connection


# ==========================================
# INPUT FILES
# ==========================================

SCHEMES_FILE ="data/processed/schemes_clean.csv"

RULES_FILE = "data/processed/eligibility_explaination.csv"


# ==========================================
# SEED SCHEMES
# ==========================================

def seed_schemes():

    print("\nLoading schemes...")

    df = pd.read_csv(SCHEMES_FILE)

    print("Number of schemes:", len(df))

    # Columns from schemes.csv
    required_columns = [
        "ID",
        "Scholarship",
        "Category",
        "Description",
        "Benefits",
        "Official_url",
        "Verification_date"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        print("\nERROR: Missing scheme columns:")
        print(missing_columns)

        return

    connection = get_connection()

    inserted_count = 0

    for _, row in df.iterrows():

        connection.execute(
            """
            INSERT OR REPLACE INTO schemes
            (
                scheme_id,
                scheme_name,
                description,
                benefits,
                category,
                state,
                official_url,
                verification_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["ID"],
                row["Scholarship"],
                row["Description"],
                row["Benefits"],
                row["Category"],
                None,
                row["Official_url"],
                row["Verification_date"]
            )
        )

        inserted_count += 1

    connection.commit()
    connection.close()

    print(f"Inserted/updated {inserted_count} schemes.")


# ==========================================
# SEED ELIGIBILITY RULES
# ==========================================

def seed_rules():

    print("\nLoading eligibility rules...")

    df = pd.read_csv(RULES_FILE)

    print("Number of rules:", len(df))

    # Columns from eligibility_rules.csv
    required_columns = [
        "rule_id",
        "scheme_id",
        "rule_type",
        "field",
        "operator",
        "value",
        "explanation",
        "version",
        "Official_url"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        print("\nERROR: Missing rule columns:")
        print(missing_columns)

        return

    df = df[required_columns].copy()

    connection = get_connection()

    inserted_count = 0

    for _, row in df.iterrows():

        connection.execute(
            """
            INSERT OR REPLACE INTO eligibility_explaination
            (
                rule_id,
                scheme_id,
                rule_type,
                field,
                operator,
                value,
                explanation,
                version,
                Official_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["rule_id"],
                row["scheme_id"],
                row["rule_type"],
                row["field"],
                row["operator"],
                row["value"],
                row["explanation"],
                row["version"],
                row["Official_url"]
            )
        )

        inserted_count += 1

    connection.commit()
    connection.close()

    print(f"Inserted/updated {inserted_count} eligibility rules.")


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    print("====================================")
    print("DATABASE SEEDING")
    print("====================================")

    seed_schemes()

    seed_rules()

    print("\nDatabase seeding completed.")