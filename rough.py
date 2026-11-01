import sqlite3

db = "data/government_schemes.db"

conn = sqlite3.connect(db)

row = conn.execute("""
SELECT
    scheme_id,
    ministry,
    target_group,
    eligibility,
    required_documents,
    application_mode
FROM schemes
WHERE scheme_id = 'C001'
""").fetchone()

print(row)

conn.close()