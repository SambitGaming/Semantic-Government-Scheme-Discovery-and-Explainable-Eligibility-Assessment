"""Monitor myScheme pages and record changes in SQLite."""

import hashlib
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from .myscheme_registry import get_source_registry

try:
    from .myscheme_registry import get_source_registry
except ImportError:
    from myscheme_registry import get_source_registry

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3

ERROR_PHRASES = [
    "access denied",
    "403 forbidden",
    "502 bad gateway",
    "503 service unavailable",
    "temporarily unavailable",
    "request blocked",
    "error. page cannot be displayed",
    "something went wrong. please try again later.",
]

FIELDS = [
    "scheme_name",
    "description",
    "benefits",
    "eligibility",
    "application_process",
    "documents_required",
    "application_mode",
    "deadline",
    "ministry_or_department",
]

SECTION_LABELS = {
    "benefits": ["benefits", "benefit"],
    "eligibility": [
        "eligibility",
        "eligibility criteria",
        "who can apply",
    ],
    "application_process": [
        "application process",
        "application procedure",
        "how to apply",
    ],
    "documents_required": [
        "documents required",
        "required documents",
    ],
    "application_mode": [
        "application mode",
        "mode of application",
    ],
    "deadline": [
        "application deadline",
        "last date",
        "deadline",
    ],
    "ministry_or_department": [
        "ministry",
        "department",
        "implementing agency",
    ],
}

STOP_HEADINGS = {
    label
    for labels in SECTION_LABELS.values()
    for label in labels
} | {
    "overview",
    "scheme details",
    "faqs",
    "frequently asked questions",
    "related schemes",
    "sources",
    "contact details",
    "references",
}


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(
        timespec="seconds"
    )


def clean(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize(value):
    return clean(value).casefold()


def content_hash(data):
    """Hash meaningful scheme fields, excluding timestamps and styling."""
    stable = {
        key: clean(data.get(key))
        for key in FIELDS
    }
    payload = json.dumps(
        stable,
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def connect_db(db_path):
    os.makedirs(
        os.path.dirname(os.path.abspath(db_path)),
        exist_ok=True,
    )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS monitored_scheme_current (
            scheme_id TEXT PRIMARY KEY,
            scheme_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            data_json TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            last_checked_at TEXT,
            last_success_at TEXT,
            verification_status TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS monitored_scheme_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id TEXT NOT NULL,
            changed_at TEXT NOT NULL,
            source_url TEXT NOT NULL,
            old_data_json TEXT,
            new_data_json TEXT NOT NULL,
            changed_fields_json TEXT NOT NULL,
            verification_status TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS monitored_source_status (
            source_id TEXT PRIMARY KEY,
            source_url TEXT NOT NULL,
            last_checked_at TEXT,
            last_success_at TEXT,
            last_http_status INTEGER,
            last_status TEXT,
            last_error TEXT
        );
    """)
    conn.commit()
    return conn


def fetch_html(url, timeout=30, max_retries=MAX_RETRIES):
    """
    Fetch a page with retries.

    Always attach the latest HTTP status to exceptions so the caller
    can record HTTP 200 error pages as well as HTTP failures.
    """
    last_status = None
    last_url = url
    last_error = "Request failed without a response."

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=timeout,
                allow_redirects=True,
            )

            last_status = response.status_code
            last_url = response.url

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type", ""
            )

            if "html" not in content_type.lower():
                raise ValueError(
                    "Expected HTML but received "
                    f"Content-Type={content_type!r}"
                )

            html = response.text
            soup = BeautifulSoup(html, "html.parser")
            visible_text = clean(soup.get_text(" ", strip=True))
            lower_text = visible_text.casefold()

            matched = next(
                (
                    phrase
                    for phrase in ERROR_PHRASES
                    if phrase in lower_text
                ),
                None,
            )

            if matched:
                raise ValueError(
                    "Source returned an error page despite "
                    f"HTTP {last_status}: {matched}"
                )

            return html, last_status, last_url

        except (requests.RequestException, ValueError) as exc:
            last_error = str(exc)

            if attempt < max_retries:
                print(
                    f"[RETRY] Attempt {attempt}/{max_retries} "
                    f"failed for {url}: {last_error}"
                )
                time.sleep(RETRY_DELAY_SECONDS)

    error = RuntimeError(
        f"Fetch failed after {max_retries} attempts: {last_error}"
    )
    error.http_status = last_status
    error.final_url = last_url
    raise error


def get_visible_lines(html):
    """Extract visible text while preserving heading boundaries."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all([
        "script",
        "style",
        "noscript",
        "svg",
        "nav",
        "footer",
    ]):
        tag.decompose()

    lines = []

    for element in soup.find_all([
        "h1",
        "h2",
        "h3",
        "h4",
        "p",
        "li",
        "dt",
        "dd",
    ]):
        text = clean(element.get_text(" ", strip=True))
        if text and text not in lines:
            lines.append(text)

    if len(lines) < 5:
        fallback = BeautifulSoup(html, "html.parser")

        for tag in fallback.find_all([
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "footer",
        ]):
            tag.decompose()

        lines = [
            clean(line)
            for line in fallback.get_text("\n").splitlines()
            if clean(line)
        ]

    return lines


def extract_section(lines, labels):
    result = []
    started = False

    normalized_labels = {label.casefold() for label in labels}

    for line in lines:
        heading = clean(line).casefold().rstrip(": ")

        if not started and heading in normalized_labels:
            started = True
            continue

        if started and heading in STOP_HEADINGS:
            break

        if started:
            result.append(line)

    return "\n".join(result).strip()


def extract_scheme(html, expected_name, source_url):
    lines = get_visible_lines(html)

    if len(lines) < 5:
        raise ValueError(
            "Too little readable page text; "
            "possible JavaScript-only or error page."
        )

    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find("h1")
    title_tag = soup.find("title")

    page_name = ""

    if heading:
        page_name = clean(heading.get_text(" ", strip=True))

    if not page_name and title_tag:
        page_name = clean(title_tag.get_text(" ", strip=True))

    if not page_name or page_name.casefold() in {
        "home",
        "myscheme",
        "my scheme",
    }:
        page_name = expected_name

    section_start = next(
        (
            index
            for index, line in enumerate(lines)
            if line.casefold().rstrip(": ") in STOP_HEADINGS
        ),
        len(lines),
    )

    description_candidates = [
        line
        for line in lines[:section_start]
        if len(line) >= 40
        and line.casefold() != page_name.casefold()
        and line.casefold() != expected_name.casefold()
    ]

    description = "\n".join(description_candidates[-4:]).strip()

    data = {
        "scheme_name": page_name,
        "description": description[:6000],
        "source_url": source_url,
        "extracted_at": now_iso(),
    }

    for field, labels in SECTION_LABELS.items():
        data[field] = extract_section(lines, labels)[:10000]

    return data


def is_usable(data):
    """Reject incomplete extractions instead of saving bad snapshots."""
    name = clean(data.get("scheme_name"))
    description = clean(data.get("description"))

    populated_sections = sum(
        bool(clean(data.get(field)))
        for field in [
            "benefits",
            "eligibility",
            "application_process",
            "documents_required",
        ]
    )

    return (
        bool(name)
        and len(description) >= 30
        and populated_sections >= 1
    )


def save_source_status(
    conn,
    source,
    status,
    http_status=None,
    error=None,
    successful=False,
):
    checked_at = now_iso()
    last_success = checked_at if successful else None

    conn.execute("""
        INSERT INTO monitored_source_status (
            source_id,
            source_url,
            last_checked_at,
            last_success_at,
            last_http_status,
            last_status,
            last_error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_id) DO UPDATE SET
            source_url = excluded.source_url,
            last_checked_at = excluded.last_checked_at,
            last_success_at = CASE
                WHEN ? = 1 THEN excluded.last_success_at
                ELSE monitored_source_status.last_success_at
            END,
            last_http_status = excluded.last_http_status,
            last_status = excluded.last_status,
            last_error = excluded.last_error
    """, (
        source["source_id"],
        source["url"],
        checked_at,
        last_success,
        http_status,
        status,
        error,
        1 if successful else 0,
    ))


def monitor_one(conn, source, delay_seconds=1.0):
    scheme_id = source["scheme_id"]
    http_status = None

    print(f"[CHECK] {scheme_id}: {source['scheme_name']}")

    try:
        html, http_status, final_url = fetch_html(source["url"])

        candidate = extract_scheme(
            html,
            source["scheme_name"],
            final_url,
        )

        if not is_usable(candidate):
            raise ValueError(
                "Extracted content is incomplete; "
                "existing data retained."
            )

        new_hash = content_hash(candidate)

        old_row = conn.execute("""
            SELECT data_json, content_hash
            FROM monitored_scheme_current
            WHERE scheme_id = ?
        """, (scheme_id,)).fetchone()

        checked_at = now_iso()

        if old_row is None:
            status = "needs_review"

            conn.execute("""
                INSERT INTO monitored_scheme_current (
                    scheme_id,
                    scheme_name,
                    source_url,
                    data_json,
                    content_hash,
                    last_checked_at,
                    last_success_at,
                    verification_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scheme_id,
                candidate["scheme_name"],
                final_url,
                json.dumps(candidate, ensure_ascii=False),
                new_hash,
                checked_at,
                checked_at,
                status,
            ))

            changed_fields = list(FIELDS)
            old_json = None

            print(f"[NEW] {scheme_id}: initial snapshot saved")

        elif old_row["content_hash"] != new_hash:
            old_data = json.loads(old_row["data_json"])

            changed_fields = [
                field
                for field in FIELDS
                if normalize(old_data.get(field))
                != normalize(candidate.get(field))
            ]

            status = "change_detected_needs_review"
            old_json = json.dumps(
                old_data,
                ensure_ascii=False,
            )

            conn.execute("""
                UPDATE monitored_scheme_current
                SET scheme_name = ?,
                    source_url = ?,
                    data_json = ?,
                    content_hash = ?,
                    last_checked_at = ?,
                    last_success_at = ?,
                    verification_status = ?
                WHERE scheme_id = ?
            """, (
                candidate["scheme_name"],
                final_url,
                json.dumps(candidate, ensure_ascii=False),
                new_hash,
                checked_at,
                checked_at,
                status,
                scheme_id,
            ))

            print(
                f"[CHANGE] {scheme_id}: "
                + ", ".join(changed_fields)
            )

        else:
            status = "needs_review"
            changed_fields = []
            old_json = None

            conn.execute("""
                UPDATE monitored_scheme_current
                SET last_checked_at = ?,
                    last_success_at = ?,
                    source_url = ?
                WHERE scheme_id = ?
            """, (
                checked_at,
                checked_at,
                final_url,
                scheme_id,
            ))

            print(f"[OK] {scheme_id}: no meaningful field changes")

        if old_row is None or changed_fields:
            conn.execute("""
                INSERT INTO monitored_scheme_history (
                    scheme_id,
                    changed_at,
                    source_url,
                    old_data_json,
                    new_data_json,
                    changed_fields_json,
                    verification_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                scheme_id,
                checked_at,
                final_url,
                old_json,
                json.dumps(candidate, ensure_ascii=False),
                json.dumps(changed_fields, ensure_ascii=False),
                status,
            ))

        save_source_status(
            conn,
            source,
            "success",
            http_status=http_status,
            successful=True,
        )
        conn.commit()
        time.sleep(delay_seconds)

        return {
            "scheme_id": scheme_id,
            "status": "success",
            "verification_status": status,
            "changed_fields": changed_fields,
        }

    except Exception as exc:
        # fetch_html attaches the last HTTP status to its exception.
        http_status = getattr(exc, "http_status", http_status)

        save_source_status(
            conn,
            source,
            "error",
            http_status=http_status,
            error=str(exc),
        )
        conn.commit()

        print(
            f"[ERROR] {scheme_id}: {exc} "
            f"(HTTP status: {http_status})"
        )

        return {
            "scheme_id": scheme_id,
            "status": "error",
            "http_status": http_status,
            "error": str(exc),
        }


def run_monitor(db_path, scheme_ids=None):
    """Monitor every registered scheme, or a selected subset."""
    registry = get_source_registry()

    if scheme_ids:
        requested = set(scheme_ids)
        registry = [
            item
            for item in registry
            if item["scheme_id"] in requested
        ]

        found_ids = {item["scheme_id"] for item in registry}
        missing_ids = requested - found_ids

        if missing_ids:
            raise ValueError(
                "Scheme IDs not found in registry: "
                + ", ".join(sorted(missing_ids))
            )

    conn = connect_db(db_path)
    results = []

    try:
        for source in registry:
            if source["enabled"]:
                results.append(monitor_one(conn, source))
    finally:
        conn.close()

    summary = {
        "total": len(results),
        "success": sum(
            result["status"] == "success"
            for result in results
        ),
        "errors": sum(
            result["status"] == "error"
            for result in results
        ),
        "results": results,
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary


def list_monitored_schemes(db_path):
    conn = connect_db(db_path)

    try:
        rows = conn.execute("""
            SELECT scheme_id,
                   scheme_name,
                   source_url,
                   last_checked_at,
                   last_success_at,
                   verification_status
            FROM monitored_scheme_current
            ORDER BY scheme_id
        """).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_monitored_scheme(db_path, scheme_id):
    conn = connect_db(db_path)

    try:
        row = conn.execute("""
            SELECT *
            FROM monitored_scheme_current
            WHERE scheme_id = ?
        """, (scheme_id,)).fetchone()

        if row is None:
            return None

        result = dict(row)
        result["data"] = json.loads(result.pop("data_json"))
        return result
    finally:
        conn.close()


def list_changes(db_path, scheme_id=None, limit=100):
    limit = max(1, min(int(limit), 500))
    conn = connect_db(db_path)

    try:
        if scheme_id:
            rows = conn.execute("""
                SELECT *
                FROM monitored_scheme_history
                WHERE scheme_id = ?
                ORDER BY history_id DESC
                LIMIT ?
            """, (scheme_id, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT *
                FROM monitored_scheme_history
                ORDER BY history_id DESC
                LIMIT ?
            """, (limit,)).fetchall()

        results = []

        for row in rows:
            item = dict(row)

            old_json = item.pop("old_data_json")
            item["old_data"] = (
                json.loads(old_json) if old_json else None
            )

            item["new_data"] = json.loads(
                item.pop("new_data_json")
            )
            item["changed_fields"] = json.loads(
                item.pop("changed_fields_json")
            )

            results.append(item)

        return results
    finally:
        conn.close()