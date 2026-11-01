import pandas as pd

from rule_engine import evaluate_rule


def check_eligibility(user_profile, scheme_id, rules_file):
    """
    Check whether a user satisfies the rules of a scheme.
    """

    rules = pd.read_csv(rules_file)

    scheme_rules = rules[
        rules["scheme_id"].astype(str) == str(scheme_id)
    ]

    results = []

    for _, rule in scheme_rules.iterrows():

        field = rule["field"]

        user_value = user_profile.get(field)

        passed = evaluate_rule(
            user_value,
            rule["operator"],
            rule["value"]
        )

        results.append({
    "rule_id": rule["rule_id"],
    "field": field,
    "user_value": user_value,
    "operator": rule["operator"],
    "required_value": rule["value"],
    "passed": passed,
    "explanation": rule["explanation"],
    "version": rule["version"],
    "Official_url": rule["Official_url"]
})

    overall_eligible = all(
        result["passed"]
        for result in results
    )

    return {
        "scheme_id": scheme_id,
        "eligible": overall_eligible,
        "rule_results": results
    }