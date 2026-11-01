import sqlite3
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# DATABASE LOCATION
# ============================================================

DATABASE_PATH = PROJECT_ROOT / "data" / "government_schemes.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create and return a SQLite database connection.
    """

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DATABASE_PATH)

    # Return rows as dictionary-like objects
    connection.row_factory = sqlite3.Row

    # Enable foreign key support
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ============================================================
# GET ONE SCHEME
# ============================================================

def get_scheme(scheme_id):
    """
    Get complete information for one scheme.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
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
            (scheme_id,)
        )

        return cursor.fetchone()

    finally:
        connection.close()


# ============================================================
# GET RULES FOR A SCHEME
# ============================================================

def get_scheme_rules(scheme_id):
    """
    Get all eligibility rules belonging to a scheme.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM eligibility_explaination
            WHERE scheme_id = ?
            ORDER BY rule_id
            """,
            (scheme_id,)
        )

        return cursor.fetchall()

    finally:
        connection.close()


# ============================================================
# GET ALL SCHEMES
# ============================================================

def get_all_schemes():
    """
    Get all schemes with complete information.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
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
            ORDER BY scheme_name
            """
        )

        return cursor.fetchall()

    finally:
        connection.close()