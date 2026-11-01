
"""Extract scholarship candidates from HTML sections for human review."""

import re
from typing import Any


HEADING_KEYWORDS = {
    "eligibility": (
        "eligibility",
        "eligible",
        "who can apply",
        "who is eligible",
        "eligibility criteria",
        "eligibility conditions",
        "qualifying criteria",
        "selection criteria",
        "income limit",
        "income criteria",
        "age limit",
        "age criteria",
        "educational qualification",
        "academic qualification",
        "qualification required",
        "conditions for application",
    ),
    "benefits": (
        "benefit",
        "benefits",
        "scholarship amount",
        "amount of scholarship",
        "scholarship value",
        "financial assistance",
        "financial support",
        "assistance provided",
        "assistance offered",
        "fellowship amount",
        "fellowship benefits",
        "rate of scholarship",
        "award amount",
        "incentive amount",
        "funding",
        "entitlements",
        "monetary benefits",
    ),
    "documents": (
        "document",
        "documents required",
        "required documents",
        "documents needed",
        "supporting documents",
        "proof required",
        "proof of",
        "certificates required",
        "certificate",
        "certificates",
        "upload documents",
        "list of documents",
    ),
    "deadlines": (
        "last date",
        "deadline",
        "important dates",
        "closing date",
        "application date",
        "application deadline",
        "submission deadline",
        "application period",
        "opening date",
        "closing of application",
        "schedule",
        "key dates",
    ),
    "descriptions": (
        "about",
        "overview",
        "description",
        "objective",
        "objectives",
        "introduction",
        "scheme details",
        "scheme information",
        "purpose",
        "salient features",
        "about the scheme",
        "about this scheme",
        "scheme overview",
        "programme details",
        "program details",
        "scheme objective",
        "background",
    ),
    "application_process": (
        "how to apply",
        "application process",
        "application procedure",
        "procedure to apply",
        "steps to apply",
        "registration process",
        "application method",
        "how can i apply",
        "apply online",
        "application instructions",
        "process of application",
    ),
}


GENERIC_HEADINGS = {
    "page content",
    "navigation",
    "menu",
    "home",
    "about us",
    "contact us",
    "quick links",
    "related links",
    "useful links",
    "frequently asked questions",
    "faqs",
}


def clean_text(value: Any) -> str:
    """Normalize whitespace and safely convert values to text."""
    if value is None:
        return ""

    text = str(value)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def heading_matches(heading: str, keywords: tuple) -> bool:
    """Check whether a heading matches a configured phrase."""
    normalized = clean_text(heading).casefold()

    if not normalized:
        return False

    for keyword in keywords:
        phrase = re.escape(keyword.casefold())

        # Allow phrase matches at word boundaries instead of arbitrary
        # substrings, reducing unrelated matches.
        if re.search(r"(?<!\w)" + phrase + r"(?!\w)", normalized):
            return True

    return False


def unique_text(values: list) -> list:
    """Deduplicate text while preserving original order."""
    result = []
    seen = set()

    for value in values:
        normalized = clean_text(value)
        key = normalized.casefold()

        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)

    return result


def _valid_sections(page: dict) -> list:
    """Return only well-formed sections with nonempty text."""
    result = []

    sections = page.get("sections", [])

    if not isinstance(sections, list):
        return result

    for section in sections:
        if not isinstance(section, dict):
            continue

        heading = clean_text(section.get("heading", ""))
        text = clean_text(section.get("text", ""))

        if text:
            result.append({
                "heading": heading or "Page content",
                "text": text,
            })

    return result


def _limit_text(text: str, max_chars: int = 6000) -> str:
    """Keep individual field candidates manageable without losing words."""
    text = clean_text(text)

    if len(text) <= max_chars:
        return text

    shortened = text[:max_chars]
    last_space = shortened.rfind(" ")

    if last_space > max_chars * 0.8:
        shortened = shortened[:last_space]

    return shortened.rstrip(" ,;:-") + " ..."


def _is_generic_heading(heading: str) -> bool:
    return clean_text(heading).casefold() in GENERIC_HEADINGS


def extract_scheme(page: dict) -> dict:
    """
    Extract candidate scheme fields from a fetched HTML page.

    Output is a candidate record for validation and human review.
    This function does not verify eligibility or factual accuracy.
    """
    if not isinstance(page, dict):
        raise TypeError("page must be a dictionary.")

    sections = _valid_sections(page)

    field_values = {
        "eligibility": [],
        "benefits": [],
        "documents": [],
        "deadlines": [],
        "descriptions": [],
        "application_process": [],
    }

    for section in sections:
        heading = section["heading"]
        text = section["text"]

        for field_name, keywords in HEADING_KEYWORDS.items():
            if heading_matches(heading, keywords):
                field_values[field_name].append(text)

    title = clean_text(page.get("title", ""))
    meta_description = clean_text(page.get("description", ""))

    # Prefer an explicit description or overview section.
    # If absent, select the first meaningful non-navigation section.
    description_parts = unique_text(
        field_values["descriptions"]
    )

    if not description_parts and not meta_description:
        for section in sections:
            heading = section["heading"]
            text = section["text"]

            if (
                not _is_generic_heading(heading)
                and len(text) >= 40
            ):
                description_parts.append(text)
                break

    description_candidate = (
        meta_description
        if len(meta_description) >= 20
        else " ".join(description_parts)
    )

    # Some pages use the browser title as the only available title.
    # Keep it as a candidate, but do not invent a name.
    scheme_name_candidate = title

    result = {
        "scheme_name_candidate": scheme_name_candidate,
        "description_candidate": _limit_text(description_candidate),
        "eligibility_candidates": [
            _limit_text(item)
            for item in unique_text(field_values["eligibility"])
        ],
        "benefit_candidates": [
            _limit_text(item)
            for item in unique_text(field_values["benefits"])
        ],
        "document_candidates": [
            _limit_text(item)
            for item in unique_text(field_values["documents"])
        ],
        "deadline_candidates": [
            _limit_text(item)
            for item in unique_text(field_values["deadlines"])
        ],
        "application_process_candidates": [
            _limit_text(item)
            for item in unique_text(
                field_values["application_process"]
            )
        ],
        "official_url": clean_text(page.get("url", "")),
        "source_sections": sections,
        "extraction_method": clean_text(
            page.get("extraction_method", "unknown")
        ),
        "javascript_rendered": bool(
            page.get("javascript_rendered", False)
        ),
    }

    # Explicit warnings help reviewers distinguish missing data from
    # information that has actually been checked.
    issues = []

    if not result["scheme_name_candidate"]:
        issues.append("Scheme name could not be extracted.")

    if len(result["description_candidate"]) < 30:
        issues.append(
            "Description is missing or too short for reliable review."
        )

    for field, label in (
        ("eligibility_candidates", "eligibility"),
        ("benefit_candidates", "benefits"),
        ("document_candidates", "required documents"),
        ("deadline_candidates", "deadlines"),
    ):
        if not result[field]:
            issues.append(
                f"No {label} section was identified; "
                "the information may be absent or use an unrecognized heading."
            )

    result["extraction_issues"] = issues
    result["verification_status"] = "pending_review"

    return result
