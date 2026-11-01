import sys
from pathlib import Path
from unittest import result

# --------------------------------------------------
# Add src directory to Python path
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.append(str(PROJECT_ROOT / "src"))


# --------------------------------------------------
# Database
# --------------------------------------------------

from database.database import (
    get_scheme,
    get_scheme_rules,
    get_all_schemes
)


# --------------------------------------------------
# Eligibility
# --------------------------------------------------

from eligibility.rule_engine import evaluate_rule


# --------------------------------------------------
# Explanation
# --------------------------------------------------

from eligibility.explanation_generator import generate_explanation


# ==================================================
# GET SCHEME DETAILS
# ==================================================

def get_scheme_details(scheme_id):

    scheme = get_scheme(scheme_id)

    if scheme is None:
        return None

    rules = get_scheme_rules(scheme_id)

    scheme_data = dict(scheme)

    # Convert database field names to the same
    # names used in schemes.csv
    formatted_scheme = {
        "ID": scheme_data.get("scheme_id"),
        "Scholarship": scheme_data.get("scheme_name"),
        "Ministry": scheme_data.get("ministry"),
        "Category": scheme_data.get("category"),
        "Status": scheme_data.get("status"),
        "Target_group": scheme_data.get("target_group"),
        "Description": scheme_data.get("description"),
        "Eligibility": scheme_data.get("eligibility"),
        "Benefits": scheme_data.get("benefits"),
        "Required_documents": scheme_data.get("required_documents"),
        "Application_mode": scheme_data.get("application_mode"),
        "Keywords": scheme_data.get("keywords"),
        "Official_url": scheme_data.get("Official_url"),
        "Source": scheme_data.get("source"),
        "Verification_date": scheme_data.get("verification_date"),
        "Rule_version": scheme_data.get("rule_version")
    }

    return {
        "scheme": formatted_scheme,
        "rules": [dict(rule) for rule in rules]
    }


# ==================================================
# EVALUATE ELIGIBILITY
# ==================================================

def evaluate_scheme_eligibility(
    scheme_id,
    user_profile
):

    rules = get_scheme_rules(scheme_id)

    if not rules:
        return None

    rule_results = []

    for rule in rules:

        field = rule["field"]

        user_value = user_profile.get(field)

        passed = evaluate_rule(
            user_value,
            rule["operator"],
            rule["value"]
        )

        rule_results.append({
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

    result = {
        "scheme_id": scheme_id,
        "eligible": all(
            rule["passed"]
            for rule in rule_results
        ),
        "rule_results": rule_results
    }

    # Generate human-readable explanation
    explanation = generate_explanation(result)

    result["explanation"] = explanation

    return result


# ==================================================
# GET ALL SCHEMES
# ==================================================

def get_schemes():

    schemes = get_all_schemes()

    return [
        dict(scheme)
        for scheme in schemes
    ]