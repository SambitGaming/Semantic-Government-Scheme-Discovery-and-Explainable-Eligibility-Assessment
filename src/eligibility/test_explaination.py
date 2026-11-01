from eligibility_checker import check_eligibility
from explanation_generator import generate_explanation


from pathlib import Path

data_path = Path("data") / "processed" / "eligibility_explaination.csv"


user_profile = {
    "age": 22,
    "state": "Karnataka",
    "annual_income": 500000,
    "category": "SC",
    "education_level": "Undergraduate"
}


result = check_eligibility(
    user_profile,
    "C001",
    data_path
)


explanation = generate_explanation(result)


print("\n================================")
print("ELIGIBILITY EXPLANATION")
print("================================")

print("Scheme:", explanation["scheme_id"])
print("Result:", explanation["overall_result"])

print("\nSummary:")
print(explanation["summary"])


print("\nPASSED RULES")
print("------------")

for rule in explanation["passed_rules"]:

    print(
        f"✓ {rule['rule_id']} | "
        f"{rule['field']} | "
        f"User: {rule['user_value']} | "
        f"Required: {rule['operator']} "
        f"{rule['required_value']}"
    )


print("\nFAILED RULES")
print("------------")

for rule in explanation["failed_rules"]:

    print(
        f"✗ {rule['rule_id']} | "
        f"{rule['field']} | "
        f"User: {rule['user_value']} | "
        f"Required: {rule['operator']} "
        f"{rule['required_value']}"
    )

    print(
        f"  Reason: {rule['explanation']}"
    )

    if rule["Official_url"]:
        print(
            f"  Source: {rule['Official_url']}"
        )


print("\nRule Versions:")

versions = set(
    rule["version"]
    for rule in (
        explanation["passed_rules"]
        + explanation["failed_rules"]
    )
)

for version in versions:
    print(f"  Version {version}")