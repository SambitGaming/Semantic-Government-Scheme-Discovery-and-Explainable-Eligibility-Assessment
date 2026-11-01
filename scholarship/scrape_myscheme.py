"""
Scrape myScheme.gov.in scholarship pages into a CSV using Playwright.

Setup:
    python -m pip install playwright
    python -m playwright install chromium

Run from the project root:
    python scholarship/scrape_myscheme.py
    python scholarship/scrape_myscheme.py --show
    python scholarship/scrape_myscheme.py --show --delay 3

Input:
    scholarship/scholarship_links.csv

Output:
    scholarship/scholarship_details_v2.csv

Failed or incomplete pages are saved as debug_<ID>.html.
Usable records are skipped on subsequent runs.
"""

import argparse
import csv
import re
import time
from pathlib import Path

from playwright.sync_api import (
    TimeoutError as PWTimeout,
    sync_playwright,
)

# ---------------------------------------------------------
# File paths
# ---------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT = SCRIPT_DIR / "scholarship_links.csv"
OUTPUT = SCRIPT_DIR / "scholarship_details_v2.csv"

SECTION_COLUMNS = [
    "Details",
    "Benefits",
    "Eligibility",
    "Exclusions",
    "Application Process",
    "Documents Required",
    "FAQs",
    "Sources And References",
]

COLUMNS = [
    "ID",
    "Scheme Name",
    "URL",
    "Page Title",
    "Ministry",
    "Tags",
    *SECTION_COLUMNS,
    "Full Page Text",
    "Status",
]

HEADINGS = {
    "details": "Details",
    "benefits": "Benefits",
    "eligibility": "Eligibility",
    "exclusions": "Exclusions",
    "application process": "Application Process",
    "documents required": "Documents Required",
    "frequently asked questions": "FAQs",
    "faqs": "FAQs",
    "sources and references": "Sources And References",
}

NAV_NOISE = {
    "feedback",
    "check eligibility",
    "back",
    "share",
    "was this helpful?",
    "sign in",
    "cancel",
    "ok",
}

ERROR_PHRASES = [
    "something went wrong. please try again later.",
    "access denied",
    "403 forbidden",
    "502 bad gateway",
    "503 service unavailable",
    "request blocked",
]


# ---------------------------------------------------------
# Text helpers
# ---------------------------------------------------------

def clean_text(value):
    """Normalize whitespace without removing meaningful text."""
    if not value:
        return ""

    lines = []
    for line in value.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)

    return "\n".join(lines).strip()


def deduplicate_paragraphs(value):
    """Remove exact repeated paragraphs while preserving their order."""
    paragraphs = re.split(r"\n\s*\n|\n", clean_text(value))
    seen = set()
    output = []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        key = re.sub(r"\s+", " ", paragraph).casefold()

        if key not in seen:
            seen.add(key)
            output.append(paragraph)

    return "\n".join(output)


def column_for_id(anchor_id):
    """Map a section anchor ID to a CSV column."""
    anchor_id = anchor_id.lower().replace("-", " ").replace("_", " ")

    for key, column in [
        ("detail", "Details"),
        ("benefit", "Benefits"),
        ("eligib", "Eligibility"),
        ("exclu", "Exclusions"),
        ("application", "Application Process"),
        ("document", "Documents Required"),
        ("faq", "FAQs"),
        ("frequent", "FAQs"),
        ("source", "Sources And References"),
        ("reference", "Sources And References"),
    ]:
        if key in anchor_id:
            return column

    return None


# ---------------------------------------------------------
# Page extraction
# ---------------------------------------------------------

def sections_by_anchor(page):
    """
    Extract sections from elements targeted by page anchor links.
    """
    result = {}

    anchors = page.eval_on_selector_all(
        "a[href^='#']",
        """
        elements => elements
            .map(element => element.getAttribute('href').slice(1))
            .filter(Boolean)
        """,
    )

    for anchor in dict.fromkeys(anchors):
        column = column_for_id(anchor)

        if not column or result.get(column):
            continue

        # Escape quotes in IDs before building the selector.
        escaped_anchor = anchor.replace("\\", "\\\\").replace("'", "\\'")

        element = page.query_selector(
            f"[id='{escaped_anchor}']"
        )

        if not element:
            continue

        try:
            text = clean_text(element.inner_text(timeout=3000))
        except Exception:
            continue

        lines = text.splitlines()

        if (
            lines
            and lines[0].strip().casefold()
            in HEADINGS
        ):
            lines = lines[1:]

        text = deduplicate_paragraphs("\n".join(lines))

        if text:
            result[column] = text

    return result


def sections_by_heading(text, existing_columns):
    """
    Fallback: split visible page text at section headings.
    """
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    marks = []

    for index, line in enumerate(lines):
        column = HEADINGS.get(line.casefold())

        if not column:
            continue

        next_line = (
            lines[index + 1].casefold()
            if index + 1 < len(lines)
            else ""
        )

        # Ignore the row of navigation tabs.
        if next_line in HEADINGS or next_line in NAV_NOISE:
            continue

        marks.append((index, column))

    result = {}

    for mark_index, (start, column) in enumerate(marks):
        end = (
            marks[mark_index + 1][0]
            if mark_index + 1 < len(marks)
            else len(lines)
        )

        body = deduplicate_paragraphs(
            "\n".join(lines[start + 1:end])
        )

        if column not in existing_columns and body:
            # Prefer the first useful occurrence.
            result.setdefault(column, body)

    return result


def page_has_error_message(text):
    """Check whether a response resembles a generic error page."""
    lowered = text.casefold()
    return any(phrase in lowered for phrase in ERROR_PHRASES)


def scrape_one(page, url):
    """Open a scheme page and extract its content."""
    response = page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=60000,
    )

    try:
        page.wait_for_load_state(
            "networkidle",
            timeout=15000,
        )
    except PWTimeout:
        # Some sites maintain network connections.
        pass

    page.wait_for_timeout(1500)

    try:
        page_title = page.title()
    except Exception:
        page_title = ""

    try:
        full_text = clean_text(
            page.locator("body").inner_text(timeout=10000)
        )
    except Exception:
        full_text = ""

    h1 = page.locator("h1").first

    try:
        title = clean_text(h1.inner_text(timeout=3000))
    except Exception:
        title = ""

    if not title:
        title = page_title

    data = sections_by_anchor(page)

    fallback = sections_by_heading(
        full_text,
        set(data),
    )

    for column, body in fallback.items():
        data.setdefault(column, body)

    # A 200 response may still be a generic error page.
    meaningful_sections = [
        column
        for column in SECTION_COLUMNS
        if len(data.get(column, "").strip()) >= 30
    ]

    if (
        page_has_error_message(full_text)
        and not meaningful_sections
    ):
        status_code = response.status if response else "unknown"
        raise RuntimeError(
            f"Error page returned (HTTP {status_code}); "
            "scheme sections were not extracted."
        )

    # Extract ministry and tags from text before the first Details heading.
    header_lines = []

    for line in full_text.splitlines():
        if line.casefold() == "details":
            break

        header_lines.append(line.strip())

    header_lines = [
        line
        for line in header_lines
        if line
        and line.casefold() not in NAV_NOISE
        and line != title
    ]

    data["Page Title"] = title
    data["Ministry"] = header_lines[0] if header_lines else ""
    data["Tags"] = (
        " | ".join(header_lines[1:])
        if len(header_lines) > 1
        else ""
    )
    data["Full Page Text"] = full_text

    for column in SECTION_COLUMNS:
        data[column] = deduplicate_paragraphs(
            data.get(column, "")
        )

    return data


# ---------------------------------------------------------
# CSV handling
# ---------------------------------------------------------

def load_existing():
    """Load existing output so interrupted runs can resume."""
    if not OUTPUT.exists():
        return {}

    with OUTPUT.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames or "ID" not in reader.fieldnames:
            return {}

        return {
            row["ID"]: row
            for row in reader
            if row.get("ID")
        }


def is_usable_record(record):
    """
    Skip only records that have usable extracted content.

    Status alone is insufficient because older versions may
    have marked incomplete records as successful.
    """
    if not record:
        return False

    if record.get("Status") != "ok":
        return False

    details = record.get("Details", "").strip()

    if len(details) < 40:
        return False

    supporting_sections = [
        "Benefits",
        "Eligibility",
        "Application Process",
        "Documents Required",
    ]

    return any(
        len(record.get(column, "").strip()) >= 30
        for column in supporting_sections
    )


def save_all(results, order):
    """Write every available result to the output CSV."""
    with OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=COLUMNS,
            extrasaction="ignore",
        )

        writer.writeheader()

        for scheme_id in order:
            if scheme_id in results:
                writer.writerow(results[scheme_id])


def save_debug_html(page, scheme_id):
    """Save the current page HTML for troubleshooting."""
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", scheme_id)
    debug_path = SCRIPT_DIR / f"debug_{safe_id}.html"

    try:
        debug_path.write_text(
            page.content(),
            encoding="utf-8",
        )
        print(f"    Debug HTML: {debug_path}")
    except Exception as exc:
        print(f"    Could not save debug HTML: {exc}")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scrape myScheme scholarship pages."
    )

    parser.add_argument(
        "--show",
        action="store_true",
        help="Show the Chromium browser window.",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Seconds to wait between schemes.",
    )

    parser.add_argument(
        "--recheck",
        action="store_true",
        help="Re-scrape records previously marked ok.",
    )

    args = parser.parse_args()

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {INPUT}\n"
            "Create scholarship_links.csv with ID, Scheme Name, and URL columns."
        )

    with INPUT.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        rows = list(csv.DictReader(file))

    if not rows:
        raise ValueError(f"No scheme rows found in {INPUT}")

    required_columns = {"ID", "Scheme Name", "URL"}
    actual_columns = set(rows[0].keys())

    missing = required_columns - actual_columns

    if missing:
        raise ValueError(
            "Input CSV is missing required columns: "
            + ", ".join(sorted(missing))
        )

    order = [row["ID"].strip() for row in rows]
    results = load_existing()

    print(f"Input:  {INPUT}")
    print(f"Output: {OUTPUT}")
    print(f"Schemes: {len(rows)}")
    print()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=not args.show
        )

        context = browser.new_context(
            locale="en-IN",
            viewport={"width": 1365, "height": 900},
        )

        page = context.new_page()
        page.set_default_timeout(15000)

        for number, row in enumerate(rows, start=1):
            scheme_id = row["ID"].strip()
            scheme_name = row["Scheme Name"].strip()
            url = row["URL"].strip()

            previous = results.get(scheme_id)

            if (
                not args.recheck
                and is_usable_record(previous)
            ):
                print(
                    f"[{number}/{len(rows)}] "
                    f"{scheme_id} skipped (already usable)"
                )
                continue

            record = {
                column: ""
                for column in COLUMNS
            }

            record.update({
                "ID": scheme_id,
                "Scheme Name": scheme_name,
                "URL": url,
            })

            last_error = ""

            for attempt in range(1, 4):
                try:
                    extracted = scrape_one(page, url)
                    record.update(extracted)

                    filled = sum(
                        1
                        for column in SECTION_COLUMNS
                        if len(record.get(column, "").strip()) >= 30
                    )

                    has_details = (
                        len(record.get("Details", "").strip()) >= 40
                    )

                    has_supporting_section = any(
                        len(record.get(column, "").strip()) >= 30
                        for column in [
                            "Benefits",
                            "Eligibility",
                            "Application Process",
                            "Documents Required",
                        ]
                    )

                    if (
                        has_details
                        and has_supporting_section
                        and filled >= 2
                    ):
                        record["Status"] = "ok"
                    else:
                        record["Status"] = (
                            f"partial ({filled}/8 sections)"
                        )

                    last_error = ""
                    break

                except Exception as exc:
                    last_error = (
                        f"{type(exc).__name__}: {exc}"
                    )

                    print(
                        f"    Attempt {attempt}/3 failed for "
                        f"{scheme_id}: {last_error}"
                    )

                    if attempt < 3:
                        time.sleep(2 * attempt)

            if last_error:
                record["Status"] = f"error: {last_error}"
                save_debug_html(page, scheme_id)

            results[scheme_id] = record

            # Save after every scheme to preserve progress.
            save_all(results, order)

            print(
                f"[{number}/{len(rows)}] "
                f"{scheme_id} {record['Status']}"
            )

            time.sleep(max(0, args.delay))

        context.close()
        browser.close()

    successful = sum(
        1
        for record in results.values()
        if is_usable_record(record)
    )

    print()
    print("Scraping finished.")
    print(f"Usable records: {successful}")
    print(f"Input schemes: {len(rows)}")
    print(f"Output file: {OUTPUT}")
    print("Re-run the script to retry incomplete or failed records.")


if __name__ == "__main__":
    main()
