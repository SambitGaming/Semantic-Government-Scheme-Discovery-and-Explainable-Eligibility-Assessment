"""Basic duplicate checks against saved JSON records."""
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def normalize_url(value: str) -> str:
    parts = urlsplit(str(value).strip())
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def find_duplicate(
    candidate: dict,
    folders: list[Path],
    current_source_id: str,
) -> str | None:
    candidate_name = normalize_name(candidate.get("scheme_name_candidate", ""))
    candidate_url = normalize_url(candidate.get("official_url", ""))

    for folder in folders:
        if not folder.exists():
            continue
        for file_path in folder.glob("*.json"):
            if file_path.stem == current_source_id:
                continue
            try:
                saved = json.loads(file_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

            saved_name = normalize_name(saved.get("scheme_name_candidate", ""))
            saved_url = normalize_url(saved.get("official_url", ""))
            if candidate_url and saved_url and candidate_url == saved_url:
                return f"Matching official URL in {file_path.name}"
            if candidate_name and saved_name and candidate_name == saved_name:
                return f"Matching normalized scheme name in {file_path.name}"
    return None
