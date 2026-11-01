"""Basic validation. Passing checks does not mean the facts are verified."""
from urllib.parse import urlparse


def validate_scheme(scheme: dict) -> dict:
    issues = []
    name = str(scheme.get("scheme_name_candidate", "")).strip()
    url = str(scheme.get("official_url", "")).strip()
    parsed = urlparse(url)

    if not name:
        issues.append("Missing scheme name candidate")
    if parsed.scheme != "https" or not parsed.netloc:
        issues.append("Missing or invalid HTTPS source URL")
    if not str(scheme.get("description_candidate", "")).strip():
        issues.append("No description candidate detected")
    if not scheme.get("eligibility_candidates"):
        issues.append("Eligibility section not detected")
    if not scheme.get("benefit_candidates"):
        issues.append("Benefits section not detected")

    scheme["validation_issues"] = issues
    scheme["validation_status"] = "needs_review" if issues else "ready_for_review"
    scheme["verification_status"] = "pending_review"
    return scheme
