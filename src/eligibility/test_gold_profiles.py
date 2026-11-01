import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from eligibility_checker import check_eligibility

PROFILES_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/benchmark/gold_profiles.csv"))
RULES_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/eligibility_explaination.csv"))
OUTPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../results/eligibility/gold_profile_results.csv"))

def run_gold_tests():
    profiles = pd.read_csv(PROFILES_FILE)
    results = []

    for _, profile in profiles.iterrows():
        user_profile = {
            "age": profile["age"],
            "state": profile["state"],
            "annual_income": profile["annual_income"],
            "category": profile["category"],
            "education_level": profile["education_level"]
        }

        result = check_eligibility(
            user_profile,
            profile["expected_scheme_id"],
            RULES_FILE
        )

        actual_result = "Eligible" if result["eligible"] else "Not Eligible"
        expected_result = profile["expected_result"]
        passed = (actual_result == expected_result)

        results.append({
            "profile_id": profile["profile_id"],
            "scheme_id": profile["expected_scheme_id"],
            "expected_result": expected_result,
            "actual_result": actual_result,
            "test_passed": passed
        })

    results_df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    results_df.to_csv(OUTPUT_FILE, index=False)

    print("\nGold Profile Evaluation Summary")
    print("===============================")
    print(results_df.to_string(index=False))

    total = len(results_df)
    passed_count = results_df["test_passed"].sum()
    failed_count = total - passed_count
    accuracy = (passed_count / total) * 100

    print("\n-------------------------------")
    print(f"Total Profiles Evaluated: {total}")
    print(f"Passed:                   {passed_count}")
    print(f"Failed:                   {failed_count}")
    print(f"Accuracy Rate:            {accuracy:.2f}%")
    print("-------------------------------\n")

if __name__ == "__main__":
    run_gold_tests()