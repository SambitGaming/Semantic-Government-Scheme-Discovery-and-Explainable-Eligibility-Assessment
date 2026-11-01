from database import (
    get_scheme,
    get_scheme_rules,
    get_all_schemes
)


print("\n================================")
print("DATABASE FUNCTION TEST")
print("================================")


# ==========================================
# TEST 1 — ALL SCHEMES
# ==========================================

print("\n1. ALL SCHEMES")

schemes = get_all_schemes()

print("Total schemes:", len(schemes))

for scheme in schemes[:5]:

    print(
        scheme["scheme_id"],
        "|",
        scheme["scheme_name"]
    )


# ==========================================
# TEST 2 — ONE SCHEME
# ==========================================

print("\n2. SINGLE SCHEME")

if schemes:

    scheme_id = schemes[0]["scheme_id"]

    scheme = get_scheme(scheme_id)

    if scheme:

        print("Scheme ID:", scheme["scheme_id"])
        print("Scheme Name:", scheme["scheme_name"])
        print("Official URL:", scheme["official_url"])

    else:

        print("Scheme not found.")


# ==========================================
# TEST 3 — RULES
# ==========================================

print("\n3. SCHEME RULES")

if schemes:

    scheme_id = schemes[0]["scheme_id"]

    rules = get_scheme_rules(scheme_id)

    print(
        "Rules for",
        scheme_id,
        ":",
        len(rules)
    )

    for rule in rules:

        print(
            rule["rule_id"],
            "|",
            rule["field"],
            "|",
            rule["operator"],
            "|",
            rule["value"]
        )


print("\nDatabase tests completed.")