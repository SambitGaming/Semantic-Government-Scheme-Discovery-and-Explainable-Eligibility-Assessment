import pandas as pd
import os

from eligibility_checker import check_eligibility
from explanation_generator import generate_explanation


PROFILES_FILE = "data/benchmark/gold_profiles.csv"
RULES_FILE = "data/processed/eligibility_explaination.csv"
OUTPUT_FILE = "results/eligibility/explainability_results.csv"


profiles = pd.read_csv(PROFILES_FILE)

rows = []


for _, profile in profiles.iterrows():

    user_profile = {}

    for column in profiles.columns:

        if column not in [
            "profile_id",
            "expected_scheme_id",
            "expected_result"
        ]:

            user_profile[column] = profile[column]

    result = check_eligibility(
        user_profile,
        profile["expected_scheme_id"],
        RULES_FILE
    )

    explanation = generate_explanation(result)


    for rule in explanation["passed_rules"]:

        rows.append({
            "profile_id": profile["profile_id"],
            "scheme_id": explanation["scheme_id"],
            "overall_result": explanation["overall_result"],
            "rule_id": rule["rule_id"],
            "field": rule["field"],
            "user_value": rule["user_value"],
            "operator": rule["operator"],
            "required_value": rule["required_value"],
            "rule_result": "PASS",
            "explanation": rule["explanation"],
            "rule_version": rule["version"],
            "Official_url": rule["Official_url"]
        })


    for rule in explanation["failed_rules"]:

        rows.append({
            "profile_id": profile["profile_id"],
            "scheme_id": explanation["scheme_id"],
            "overall_result": explanation["overall_result"],
            "rule_id": rule["rule_id"],
            "field": rule["field"],
            "user_value": rule["user_value"],
            "operator": rule["operator"],
            "required_value": rule["required_value"],
            "rule_result": "FAIL",
            "explanation": rule["explanation"],
            "rule_version": rule["version"],
            "Official_url": rule["Official_url"]
        })


df = pd.DataFrame(rows)


os.makedirs(
    "../../results/eligibility",
    exist_ok=True
)


df.to_csv(
    OUTPUT_FILE,
    index=False
)


print()
print("================================")
print("EXPLAINABILITY RESULTS")
print("================================")

print("Saved to:")
print(OUTPUT_FILE)

print()
print("Total explanation records:", len(df))