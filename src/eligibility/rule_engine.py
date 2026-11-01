def evaluate_rule(user_value, operator, rule_value):
    """
    Evaluate a single eligibility rule.

    Returns:
        True  -> rule passed
        False -> rule failed
    """

    if user_value is None:
        return False

    if operator == "==":
        return str(user_value).lower() == str(rule_value).lower()

    elif operator == "!=":
        return str(user_value).lower() != str(rule_value).lower()

    elif operator == ">=":
        return float(user_value) >= float(rule_value)

    elif operator == "<=":
        return float(user_value) <= float(rule_value)

    elif operator == ">":
        return float(user_value) > float(rule_value)

    elif operator == "<":
        return float(user_value) < float(rule_value)

    elif operator == "IN":
        allowed_values = [
            value.strip().lower()
            for value in str(rule_value).split("|")
        ]

        return str(user_value).lower() in allowed_values

    else:
        raise ValueError(f"Unsupported operator: {operator}")