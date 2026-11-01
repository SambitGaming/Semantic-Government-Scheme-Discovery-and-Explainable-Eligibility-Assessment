
"""Fetch permitted HTTPS HTML pages and extract clean page content."""

from urllib.parse import urljoin, urlparse, urldefrag
import re

import requests
from bs4 import BeautifulSoup


TIMEOUT_SECONDS = 25
MAX_RESPONSE_BYTES = 5 * 1024 * 1024

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

ERROR_PAGE_PHRASES = (
    "error. page cannot be displayed",
    "please contact your service provider",
    "service unavailable",
    "access denied",
    "403 forbidden",
    "502 bad gateway",
    "503 service unavailable",
    "temporarily unavailable",
    "request blocked",
    "the request could not be satisfied",
    "attention required! | cloudflare",
    "verify you are human",
    "enable javascript and cookies to continue",
)

IGNORED_TAGS = (
    "script",
    "style",
    "noscript",
    "nav",
    "footer",
    "header",
    "form",
    "iframe",
    "svg",
    "canvas",
    "template",
)

IGNORED_EXTENSIONS = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".zip", ".doc", ".docx", ".xls", ".xlsx",
    ".ppt", ".pptx", ".mp4", ".mp3", ".css", ".js",
)


def clean_text(value) -> str:
    """Normalize whitespace."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def validate_https_url(url: str) -> str:
    """Reject malformed URLs and non-HTTPS schemes."""
    url = clean_text(url)
    parsed = urlparse(url)

    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Only valid HTTPS URLs are supported.")

    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("The URL contains an invalid port.") from exc

    return url


def _check_error_page(text: str, status_code: int) -> None:
    """Detect common blocking/error pages, including HTTP 200 pages."""
    normalized = clean_text(text).casefold()

    for phrase in ERROR_PAGE_PHRASES:
        if phrase.casefold() in normalized:
            raise ValueError(
                "The server returned an error or blocking page "
                f"(HTTP {status_code}): {phrase}"
            )


def _extract_links(soup: BeautifulSoup, base_url: str) -> list:
    """Extract unique, absolute HTTPS links."""
    links = []
    seen = set()

    for anchor in soup.find_all("a", href=True):
        href = clean_text(anchor.get("href"))

        if not href:
            continue

        absolute_url = urljoin(base_url, href)
        parsed = urlparse(absolute_url)

        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            continue

        if parsed.path.lower().endswith(IGNORED_EXTENSIONS):
            continue

        normalized_url, _fragment = urldefrag(absolute_url)

        if normalized_url in seen:
            continue

        seen.add(normalized_url)

        links.append({
            "text": clean_text(anchor.get_text(" ", strip=True)),
            "url": normalized_url,
        })

    return links


def _extract_sections(soup: BeautifulSoup) -> list:
    """Group paragraphs and lists under their nearest preceding heading."""
    sections = []
    current_heading = "Page content"
    current_parts = []
    seen_parts = set()

    def flush():
        nonlocal current_parts, seen_parts

        if current_parts:
            sections.append({
                "heading": current_heading,
                "text": " ".join(current_parts),
            })

        current_parts = []
        seen_parts = set()

    for element in soup.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "dt", "dd"]
    ):
        text = clean_text(element.get_text(" ", strip=True))

        if not text:
            continue

        if element.name in {
            "h1", "h2", "h3", "h4", "h5", "h6"
        }:
            flush()
            current_heading = text
            continue

        # Avoid counting a paragraph inside a list item twice.
        if element.find_parent("li") is not None and element.name == "p":
            continue

        key = text.casefold()

        if key not in seen_parts:
            seen_parts.add(key)
            current_parts.append(text)

    flush()
    return sections


def fetch_page(url: str) -> dict:
    """
    Fetch an HTTPS HTML page.

    Returns:
        title, description, url, sections, links, status_code,
        content_type, and extraction metadata.

    This function does not execute JavaScript.
    """
    url = validate_https_url(url)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-IN,en;q=0.9",
        "Cache-Control": "no-cache",
    }

    # Do not automatically follow redirects to another host.
    # Callers can inspect the redirect and decide whether to allow it.
    with requests.Session() as session:
        response = session.get(
            url,
            headers=headers,
            timeout=TIMEOUT_SECONDS,
            allow_redirects=False,
            stream=True,
        )

        try:
            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location", "")
                target = urljoin(url, location) if location else ""

                if not target:
                    raise ValueError(
                        "The server returned a redirect without a target."
                    )

                target = validate_https_url(target)

                raise ValueError(
                    "The server redirected the request. "
                    f"Redirect target: {target}. "
                    "Verify the target host before fetching it."
                )

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type", ""
            ).lower()

            if (
                "text/html" not in content_type
                and "application/xhtml+xml" not in content_type
            ):
                raise ValueError(
                    "Unsupported content type: "
                    f"{content_type or 'unknown'}. "
                    "Only HTML pages are supported."
                )

            content_length = response.headers.get("Content-Length")

            if content_length:
                try:
                    if int(content_length) > MAX_RESPONSE_BYTES:
                        raise ValueError(
                            "HTML response exceeds the configured size limit."
                        )
                except ValueError as exc:
                    if "size limit" in str(exc):
                        raise

            chunks = []
            total_bytes = 0

            for chunk in response.iter_content(chunk_size=65536):
                if not chunk:
                    continue

                total_bytes += len(chunk)

                if total_bytes > MAX_RESPONSE_BYTES:
                    raise ValueError(
                        "HTML response exceeds the configured size limit."
                    )

                chunks.append(chunk)

            encoding = response.encoding or "utf-8"
            html = b"".join(chunks).decode(
                encoding, errors="replace"
            )
            final_url = response.url
            status_code = response.status_code

        finally:
            response.close()

    soup = BeautifulSoup(html, "html.parser")

    # Inspect the page before removing elements.
    original_text = clean_text(soup.get_text(" ", strip=True))
    _check_error_page(original_text, status_code)

    title = (
        clean_text(soup.title.get_text(" ", strip=True))
        if soup.title
        else ""
    )

    meta_tag = soup.find(
        "meta",
        attrs={"name": re.compile(r"^description$", re.I)},
    )

    if not meta_tag:
        meta_tag = soup.find(
            "meta",
            attrs={"property": re.compile(r"^og:description$", re.I)},
        )

    description = clean_text(
        meta_tag.get("content", "") if meta_tag else ""
    )

    # Collect links before removing navigation elements.
    links = _extract_links(soup, final_url)

    # Remove non-content elements and common boilerplate.
    for element in soup(list(IGNORED_TAGS)):
        element.decompose()

    # Remove elements explicitly marked as common page furniture.
    for element in soup.find_all(True):
        classes = " ".join(element.get("class", []))
        identifier = element.get("id", "")
        marker = f"{classes} {identifier}".casefold()

        if re.search(
            r"(^|[\s_-])(cookie|breadcrumb|social-share|"
            r"advertisement|advert|sidebar|site-nav|"
            r"pagination)([\s_-]|$)",
            marker,
        ):
            element.decompose()

    sections = _extract_sections(soup)

    extracted_text = clean_text(
        " ".join(section["text"] for section in sections)
    )

    if len(extracted_text) < 20 and len(description) < 20:
        raise ValueError(
            "The page contains insufficient extractable text. "
            "It may require JavaScript rendering, an API, or manual review."
        )

    return {
        "title": title,
        "description": description,
        "url": final_url,
        "sections": sections,
        "links": links,
        "status_code": status_code,
        "content_type": content_type,
        "extraction_method": "requests_beautifulsoup",
        "javascript_rendered": False,
    }
