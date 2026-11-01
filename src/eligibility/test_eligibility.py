from eligibility_checker import check_eligibility


user_profile = {
    "age": 22,
    "state": "Karnataka",
    "annual_income": 200000,
    "category": "SC",
    "education_level": "Undergraduate"
}


result = check_eligibility(
    user_profile,
    "C001",
    "../../data/processed/eligibility_explaination.csv"
)


print("\nEligibility Result")
print("===================")

print("Scheme:", result["scheme_id"])
print("Eligible:", result["eligible"])

print("\nRule Results:")

for rule in result["rule_results"]:

    print(
        f"{rule['rule_id']} | "
        f"{rule['field']} | "
        f"User value: {rule['user_value']} | "
        f"Required: {rule['required_value']} | "
        f"Passed: {rule['passed']}"
    )

    print(f"Explanation: {rule['explanation']}")
    print(f"Rule version: {rule['version']}")
    print()