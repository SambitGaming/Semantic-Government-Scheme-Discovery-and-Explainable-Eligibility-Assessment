def generate_explanation(result):
    """
    Convert an eligibility result into a
    human-readable explanation.
    """

    scheme_id = result["scheme_id"]
    eligible = result["eligible"]

    if eligible:
        overall_result = "Eligible"
    else:
        overall_result = "Not Eligible"

    explanation = {
        "scheme_id": scheme_id,
        "overall_result": overall_result,
        "passed_rules": [],
        "failed_rules": [],
        "summary": ""
    }

    for rule in result["rule_results"]:

        rule_info = {
            "rule_id": rule["rule_id"],
            "field": rule["field"],
            "user_value": rule["user_value"],
            "required_value": rule["required_value"],
            "operator": rule["operator"],
            "explanation": rule["explanation"],
            "version": rule["version"],
            "Official_url": rule.get("Official_url", "")
        }

        if rule["passed"]:
            explanation["passed_rules"].append(rule_info)
        else:
            explanation["failed_rules"].append(rule_info)

    if eligible:

        explanation["summary"] = (
            "The applicant satisfies all mandatory "
            "eligibility rules evaluated for this scheme."
        )

    else:

        failed_count = len(
            explanation["failed_rules"]
        )

        explanation["summary"] = (
            f"The applicant does not satisfy "
            f"{failed_count} mandatory eligibility rule(s)."
        )

    return explanation