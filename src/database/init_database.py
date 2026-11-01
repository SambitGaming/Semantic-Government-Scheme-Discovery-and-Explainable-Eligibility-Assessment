from database import get_connection


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # ==========================================
    # SCHEMES TABLE
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schemes (
            scheme_id TEXT PRIMARY KEY,
            scheme_name TEXT NOT NULL,
            description TEXT,
            benefits TEXT,
            category TEXT,
            state TEXT,
            Official_url TEXT,
            verification_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ==========================================
    # ELIGIBILITY RULES TABLE
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eligibility_explaination (
            rule_id TEXT PRIMARY KEY,
            scheme_id TEXT NOT NULL,
            rule_type TEXT,
            field TEXT NOT NULL,
            operator TEXT NOT NULL,
            value TEXT NOT NULL,
            explanation TEXT,
            version TEXT NOT NULL,
            Official_url TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (scheme_id)
                REFERENCES schemes(scheme_id)
        )
    """)

    # ==========================================
    # RULE VERSIONS TABLE
    # ==========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rule_versions (
            version_id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id TEXT NOT NULL,
            version TEXT NOT NULL,
            effective_date TEXT,
            source_url TEXT,
            notes TEXT,

            FOREIGN KEY (scheme_id)
                REFERENCES schemes(scheme_id)
        )
    """)

    connection.commit()

    connection.close()

    print("===================================")
    print("Database initialized successfully")
    print("===================================")


if __name__ == "__main__":
    initialize_database()