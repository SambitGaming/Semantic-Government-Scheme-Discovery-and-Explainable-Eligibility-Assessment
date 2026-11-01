"""Fetch registered myScheme pages and save their readable contents."""

import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import truststore

# Use Windows certificate-store integration before importing requests.
truststore.inject_into_ssl()

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.automation.myscheme_registry import OFFICIAL_SOURCES


OUTPUT_DIR = PROJECT_ROOT / "data" / "automation" / "fetched_schemes"
LOG_DIR = PROJECT_ROOT / "data" / "automation" / "logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_DIR / "extraction_bot.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)

REQUEST_TIMEOUT = 25
REQUEST_DELAY_SECONDS = 1

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-IN,en;q=0.9",
}

REMOVE_TAGS = [
    "script",
    "style",
    "noscript",
    "svg",
    "nav",
    "footer",
    "header",
    "form",
]

FIELD_KEYWORDS = {
    "description": (
        "about the scheme",
        "overview",
        "objective",
        "description",
        "scheme details",
        "introduction",
    ),
    "eligibility": (
        "eligibility",
        "who can apply",
        "eligible",
        "eligibility criteria",
    ),
    "benefits": (
        "benefits",
        "scholarship amount",
        "financial assistance",
        "amount of scholarship",
        "assistance provided",
    ),
    "documents_required": (
        "documents required",
        "required documents",
        "documents",
        "supporting documents",
    ),
    "application_process": (
        "application process",
        "how to apply",
        "application procedure",
        "procedure to apply",
    ),
    "deadline": (
        "last date",
        "deadline",
        "important dates",
        "closing date",
    ),
}


def clean_text(value):
    """Normalize whitespace in extracted text."""
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_filename(value):
    """Convert a source ID into a safe filename."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", str(value))


def write_json(path, data):
    """Save JSON atomically."""
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(path)


def heading_field(heading):
    """Map a section heading to a known scheme field."""
    normalized = clean_text(heading).casefold()

    for field, keywords in FIELD_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return field

    return None


def fetch_scheme(source):
    """Fetch a registered scheme URL and extract its page content."""
    source_id = source["source_id"]
    scheme_name = source["name"]
    url = source["url"]

    parsed = urlparse(url)

    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"Invalid HTTPS URL: {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()

    if "html" not in content_type:
        raise ValueError(
            f"Unsupported response content type: {content_type}"
        )

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in REMOVE_TAGS:
        for element in soup.find_all(tag):
            element.decompose()

    # Capture the readable text and section headings.
    page_title = clean_text(
        soup.title.get_text(" ", strip=True) if soup.title else ""
    )

    sections = []
    current_heading = "Overview"
    current_parts = []

    for element in soup.find_all(
        ["h1", "h2", "h3", "h4", "p", "li"]
    ):
        text = clean_text(element.get_text(" ", strip=True))

        if not text:
            continue

        if element.name in ("h1", "h2", "h3", "h4"):
            if current_parts:
                sections.append({
                    "heading": current_heading,
                    "text": clean_text(" ".join(current_parts)),
                })

            current_heading = text
            current_parts = []
        else:
            current_parts.append(text)

    if current_parts:
        sections.append({
            "heading": current_heading,
            "text": clean_text(" ".join(current_parts)),
        })

    # Some sites expose a short description in metadata.
    meta = soup.find(
        "meta",
        attrs={"name": re.compile("^description$", re.I)},
    )
    meta_description = clean_text(
        meta.get("content", "") if meta else ""
    )

    fields = {
        "description": meta_description,
        "eligibility": [],
        "benefits": [],
        "documents_required": [],
        "application_process": [],
        "deadline": [],
    }

    for section in sections:
        field = heading_field(section["heading"])
        if field:
            if field == "description":
                fields[field] = (
                    fields[field] or section["text"]
                )
            else:
                fields[field].append(section["text"])

    # Fallback description from the first meaningful section.
    if not fields["description"]:
        for section in sections:
            if len(section["text"]) >= 40:
                fields["description"] = section["text"]
                break

    # Remove duplicate field values while preserving order.
    for field, value in fields.items():
        if isinstance(value, list):
            fields[field] = list(dict.fromkeys(value))

    # Preserve all extracted sections even if their headings are unfamiliar.
    full_text = clean_text(
        " ".join(section["text"] for section in sections)
    )

    if not full_text and not fields["description"]:
        raise ValueError(
            "No readable scheme text found. The site may require "
            "JavaScript rendering or may have blocked the request."
        )

    return {
        "source_id": source_id,
        "scheme_name": scheme_name,
        "registered_url": url,
        "final_url": response.url,
        "page_title": page_title,
        **fields,
        "full_text": full_text,
        "sections": sections,
        "http_status": response.status_code,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "verification_status": "needs_review",
        "fetch_status": "success",
    }


def process_source(source):
    """Fetch one source and save either its content or its error."""
    source_id = safe_filename(source["source_id"])
    output_path = OUTPUT_DIR / f"{source_id}.json"

    try:
        record = fetch_scheme(source)
        write_json(output_path, record)

        print(f"[OK] {source['source_id']} - {source['name']}")
        print(f"     Saved: {output_path.name}")
        print(f"     Text length: {len(record['full_text'])} characters")

        logging.info(
            "Fetched %s successfully from %s",
            source["source_id"],
            source["url"],
        )

        return True

    except (RequestException, ValueError) as exc:
        record = {
            "source_id": source["source_id"],
            "scheme_name": source["name"],
            "registered_url": source["url"],
            "fetch_status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
            "verification_status": "needs_review",
        }

        write_json(output_path, record)

        logging.warning(
            "Failed to fetch %s (%s): %s",
            source["source_id"],
            source["url"],
            exc,
        )

        print(f"[FAILED] {source['source_id']} - {source['name']}")
        print(f"         {exc}")
        return False


def run_bot():
    """Fetch all enabled schemes in the registry."""
    enabled_sources = [
        source
        for source in OFFICIAL_SOURCES
        if source.get("enabled") is True
    ]

    if not enabled_sources:
        print(
            "No enabled sources configured. Check OFFICIAL_SOURCES "
            "in src/automation/myscheme_registry.py."
        )
        return

    print(f"Fetching {len(enabled_sources)} registered scheme pages...")

    succeeded = 0
    failed = 0

    for source in enabled_sources:
        if process_source(source):
            succeeded += 1
        else:
            failed += 1

        time.sleep(REQUEST_DELAY_SECONDS)

    print("\nFetch summary")
    print("-------------")
    print(f"Registered and enabled: {len(enabled_sources)}")
    print(f"Fetched successfully: {succeeded}")
    print(f"Failed: {failed}")
    print(f"JSON output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    run_bot()