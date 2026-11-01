import sqlite3
import csv
import shutil
from pathlib import Path
from datetime import datetime


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "data" / "government_schemes.db"
CSV_PATH = PROJECT_ROOT / "data" / "raw" /"schemes.csv"


# ============================================================
# DATABASE COLUMNS REQUIRED BY THE PROJECT
# ============================================================

REQUIRED_COLUMNS = {
    "ministry": "TEXT",
    "status": "TEXT",
    "target_group": "TEXT",
    "eligibility": "TEXT",
    "required_documents": "TEXT",
    "application_mode": "TEXT",
    "keywords": "TEXT",
    "source": "TEXT",
    "rule_version": "TEXT",
}


# ============================================================
# CSV → DATABASE COLUMN MAPPING
# ============================================================

CSV_MAPPING = {
    "ID": "scheme_id",
    "Scholarship": "scheme_name",
    "Ministry": "ministry",
    "Category": "category",
    "Status": "status",
    "Target_group": "target_group",
    "Description": "description",
    "Eligibility": "eligibility",
    "Benefits": "benefits",
    "Required_documents": "required_documents",
    "Application_mode": "application_mode",
    "Keywords": "keywords",
    "Official_url": "Official_url",
    "Source": "source",
    "Verification_date": "verification_date",
    "Rule_version": "rule_version",
}


# ============================================================
# BACKUP
# ============================================================

def create_backup():
    if not DATABASE_PATH.exists():
        print("Database file not found:")
        print(DATABASE_PATH)
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_path = DATABASE_PATH.with_name(
        f"government_schemes_backup_{timestamp}.db"
    )

    shutil.copy2(DATABASE_PATH, backup_path)

    print("Database backup created:")
    print(backup_path)

    return True


# ============================================================
# CHECK EXISTING COLUMNS
# ============================================================

def get_existing_columns(connection):
    cursor = connection.execute(
        "PRAGMA table_info(schemes)"
    )

    return {
        row[1]
        for row in cursor.fetchall()
    }


# ============================================================
# ADD MISSING COLUMNS
# ============================================================

def add_missing_columns(connection):
    existing_columns = get_existing_columns(connection)

    print("\nExisting columns:")
    print(existing_columns)

    for column_name, column_type in REQUIRED_COLUMNS.items():

        if column_name not in existing_columns:

            print(f"Adding missing column: {column_name}")

            connection.execute(
                f"ALTER TABLE schemes ADD COLUMN {column_name} {column_type}"
            )

        else:
            print(f"Column already exists: {column_name}")


# ============================================================
# IMPORT CSV DATA
# ============================================================

def import_csv(connection):

    if not CSV_PATH.exists():

        print("\nERROR: schemes.csv was not found.")
        print("Expected location:")
        print(CSV_PATH)

        return

    print("\nReading CSV:")
    print(CSV_PATH)

    with open(
        CSV_PATH,
        "r",
        encoding="cp1252",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        print("\nCSV columns:")
        print(reader.fieldnames)

        imported = 0
        inserted = 0
        updated = 0

        for row in reader:

            scheme_id = row.get("ID")

            if not scheme_id:
                continue

            # ------------------------------------------------
            # Prepare values
            # ------------------------------------------------

            values = {}

            for csv_column, db_column in CSV_MAPPING.items():

                value = row.get(csv_column)

                if value is None:
                    value = ""

                values[db_column] = value.strip()

            # ------------------------------------------------
            # Check whether scheme already exists
            # ------------------------------------------------

            existing = connection.execute(
                """
                SELECT scheme_id
                FROM schemes
                WHERE scheme_id = ?
                """,
                (scheme_id,)
            ).fetchone()

            if existing:

                # --------------------------------------------
                # UPDATE
                # --------------------------------------------

                connection.execute(
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
                        values["scheme_name"],
                        values["ministry"],
                        values["category"],
                        values["status"],
                        values["target_group"],
                        values["description"],
                        values["eligibility"],
                        values["benefits"],
                        values["required_documents"],
                        values["application_mode"],
                        values["keywords"],
                        values["Official_url"],
                        values["source"],
                        values["verification_date"],
                        values["rule_version"],
                        scheme_id,
                    )
                )

                updated += 1

            else:

                # --------------------------------------------
                # INSERT
                # --------------------------------------------

                connection.execute(
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
                    (
                        values["scheme_id"],
                        values["scheme_name"],
                        values["ministry"],
                        values["category"],
                        values["status"],
                        values["target_group"],
                        values["description"],
                        values["eligibility"],
                        values["benefits"],
                        values["required_documents"],
                        values["application_mode"],
                        values["keywords"],
                        values["Official_url"],
                        values["source"],
                        values["verification_date"],
                        values["rule_version"],
                    )
                )

                inserted += 1

            imported += 1

    print("\nCSV import completed.")
    print(f"Rows processed : {imported}")
    print(f"Rows updated   : {updated}")
    print(f"Rows inserted  : {inserted}")


# ============================================================
# VERIFY DATABASE
# ============================================================

def verify_database(connection):

    print("\n" + "=" * 60)
    print("DATABASE VERIFICATION")
    print("=" * 60)

    columns = connection.execute(
        "PRAGMA table_info(schemes)"
    ).fetchall()

    print("\nCurrent schemes table columns:")

    for column in columns:
        print(f"- {column[1]}")

    # --------------------------------------------------------
    # Check C001
    # --------------------------------------------------------

    row = connection.execute(
        """
        SELECT
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
        FROM schemes
        WHERE scheme_id = ?
        """,
        ("C001",)
    ).fetchone()

    if row:

        print("\nC001 found successfully.")

        print("\nC001 basic information:")

        print("ID          :", row[0])
        print("Scholarship :", row[1])
        print("Ministry    :", row[2])
        print("Category    :", row[3])
        print("Status      :", row[4])
        print("Target group:", row[5])
        print("Official URL:", row[12])

    else:

        print("\nWARNING: C001 was not found.")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DATABASE MIGRATION")
    print("=" * 60)

    print("\nDatabase:")
    print(DATABASE_PATH)

    print("\nCSV:")
    print(CSV_PATH)

    # --------------------------------------------------------
    # Backup first
    # --------------------------------------------------------

    if not create_backup():
        return

    # --------------------------------------------------------
    # Connect
    # --------------------------------------------------------

    connection = sqlite3.connect(DATABASE_PATH)

    try:

        # ----------------------------------------------------
        # Make sure schemes table exists
        # ----------------------------------------------------

        table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name='schemes'
            """
        ).fetchone()

        if not table:

            print("\nERROR: schemes table does not exist.")

            return

        # ----------------------------------------------------
        # Add missing columns
        # ----------------------------------------------------

        add_missing_columns(connection)

        # ----------------------------------------------------
        # Import CSV
        # ----------------------------------------------------

        import_csv(connection)

        # ----------------------------------------------------
        # Save changes
        # ----------------------------------------------------

        connection.commit()

        # ----------------------------------------------------
        # Verify
        # ----------------------------------------------------

        verify_database(connection)

    except Exception as error:

        connection.rollback()

        print("\nERROR:")
        print(error)

        print("\nChanges were rolled back.")

    finally:

        connection.close()

    print("\nMigration finished.")


if __name__ == "__main__":
    main()