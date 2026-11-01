from database import get_connection


connection = get_connection()

cursor = connection.cursor()


# ==========================================
# COUNT SCHEMES
# ==========================================

cursor.execute(
    "SELECT COUNT(*) AS count FROM schemes"
)

scheme_count = cursor.fetchone()["count"]

print("\nSCHEME COUNT")
print("============")
print(scheme_count)


# ==========================================
# COUNT RULES
# ==========================================

cursor.execute(
    "SELECT COUNT(*) AS count FROM eligibility_explaination"
)

rule_count = cursor.fetchone()["count"]

print("\nRULE COUNT")
print("==========")
print(rule_count)


# ==========================================
# SHOW SCHEMES
# ==========================================

print("\nSCHEMES")
print("=======")

cursor.execute("""
    SELECT scheme_id, scheme_name
    FROM schemes
    LIMIT 10
""")

for row in cursor.fetchall():

    print(
        row["scheme_id"],
        "|",
        row["scheme_name"]
    )


# ==========================================
# SHOW RULES
# ==========================================

print("\nELIGIBILITY RULES")
print("=================")

cursor.execute("""
    SELECT
        rule_id,
        scheme_id,
        field,
        operator,
        value
    FROM eligibility_explaination
    LIMIT 10
""")

for row in cursor.fetchall():

    print(
        row["rule_id"],
        "|",
        row["scheme_id"],
        "|",
        row["field"],
        "|",
        row["operator"],
        "|",
        row["value"]
    )


connection.close()