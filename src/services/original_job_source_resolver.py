import html
import os
import re
from urllib.parse import (
    parse_qs,
    unquote,
    urljoin,
    urlparse,
)

import httpx


SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"
SEARCH_TIMEOUT_SECONDS = 8.0

AGGREGATOR_HOST_HINTS = (
    "jooble.org",
    "jooble.com",
    "linkedin.com",
    "indeed.com",
    "jobstreet.com",
    "jobsdb.com",
    "glassdoor.com",
    "foundit.sg",
    "foundit.com",
    "google.com",
    "googleusercontent.com",
)

ATS_HOST_HINTS = (
    "greenhouse.io",
    "greenhouse.com",
    "lever.co",
    "smartrecruiters.com",
    "myworkdayjobs.com",
    "myworkdaysite.com",
    "ashbyhq.com",
    "successfactors.com",
)

REDIRECT_QUERY_KEYS = {
    "url",
    "u",
    "target",
    "destination",
    "dest",
    "redirect",
    "redirect_url",
    "redirecturl",
    "to",
    "link",
    "apply",
    "apply_url",
    "applyurl",
    "out",
    "out_url",
    "outurl",
}

URL_ATTRIBUTE_PATTERN = re.compile(
    r"(?:href|action|data-href|data-url|data-link|data-apply-url|data-applyurl)"
    r"\s*=\s*[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)

ABSOLUTE_URL_PATTERN = re.compile(
    r"https?:\\?/\\?/[^\"'<>\s]+",
    re.IGNORECASE,
)


def _metadata_dict(job):
    metadata = job.get("source_metadata") or {}

    if isinstance(metadata, str):
        try:
            import json
            metadata = json.loads(metadata)
        except Exception:
            metadata = {}

    return metadata if isinstance(metadata, dict) else {}


def host_for_url(url):
    try:
        return (urlparse(str(url or "")).hostname or "").casefold()
    except ValueError:
        return ""


def is_aggregator_url(url):
    host = host_for_url(url)
    return any(hint in host for hint in AGGREGATOR_HOST_HINTS)


def is_ats_url(url):
    host = host_for_url(url)
    return any(hint in host for hint in ATS_HOST_HINTS)


def cached_original_source(job):
    metadata = _metadata_dict(job)
    url = str(metadata.get("resolved_source_url") or "").strip()

    if not url:
        return None

    return {
        "url": url,
        "method": str(
            metadata.get("resolved_source_method")
            or "cached_original_source"
        ),
        "confidence": float(
            metadata.get("resolved_source_confidence")
            or 1.0
        ),
    }


def _unwrap_redirect_url(raw_url):
    """Recover an embedded destination from tracking/redirect URLs."""

    candidate = html.unescape(str(raw_url or "")).strip().replace("\\/", "/")
    if not candidate:
        return None

    for _ in range(4):
        decoded = unquote(candidate)
        if decoded == candidate:
            break
        candidate = decoded

    try:
        parsed = urlparse(candidate)
    except ValueError:
        return None

    if parsed.scheme not in {"http", "https"}:
        return None

    query = parse_qs(parsed.query)
    for key, values in query.items():
        normalized_key = re.sub(r"[^a-z0-9]+", "", key.casefold())
        if normalized_key not in {
            re.sub(r"[^a-z0-9]+", "", item)
            for item in REDIRECT_QUERY_KEYS
        }:
            continue

        for value in values:
            nested = html.unescape(str(value or "")).replace("\\/", "/").strip()
            for _ in range(3):
                decoded = unquote(nested)
                if decoded == nested:
                    break
                nested = decoded

            try:
                nested_parsed = urlparse(nested)
            except ValueError:
                continue

            if (
                nested_parsed.scheme in {"http", "https"}
                and nested_parsed.hostname
            ):
                return nested

    return candidate


def discover_outbound_source_urls(html_text, base_url):
    """Extract likely original employer/ATS destinations from an aggregator page."""

    candidates = []

    def add(raw_url, context=""):
        if not raw_url:
            return

        value = html.unescape(str(raw_url)).strip().replace("\\/", "/")
        if value.startswith(("mailto:", "javascript:", "tel:", "#")):
            return

        value = urljoin(base_url, value)
        unwrapped = _unwrap_redirect_url(value)
        if unwrapped:
            value = unwrapped

        try:
            parsed = urlparse(value)
        except ValueError:
            return

        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return

        if value == base_url:
            return

        lowered = value.casefold().split("?", 1)[0]
        if lowered.endswith(
            (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".pdf")
        ):
            return

        item = {
            "url": value,
            "context": re.sub(r"\s+", " ", context or "").strip(),
        }

        if not any(existing["url"] == value for existing in candidates):
            candidates.append(item)

    for match in URL_ATTRIBUTE_PATTERN.finditer(html_text or ""):
        start = max(0, match.start() - 160)
        end = min(len(html_text or ""), match.end() + 160)
        add(match.group(1), (html_text or "")[start:end])

    for match in ABSOLUTE_URL_PATTERN.finditer(html_text or ""):
        add(match.group(0).replace("\\/", "/"), "embedded absolute URL")

    for match in re.finditer(
        r"<meta\b[^>]*http-equiv=[\"']?refresh[\"']?[^>]*content=[\"']([^\"']+)[\"'][^>]*>",
        html_text or "",
        re.IGNORECASE,
    ):
        content = match.group(1)
        url_match = re.search(r"url\s*=\s*(.+)$", content, re.IGNORECASE)
        if url_match:
            add(url_match.group(1).strip(" '\""), "meta refresh")

    def score(item):
        url = item["url"]
        context = item["context"].casefold()
        host = host_for_url(url)

        applyish = any(
            token in context
            for token in (
                "apply",
                "view job",
                "view original",
                "company website",
                "employer",
                "career",
                "position",
                "vacancy",
            )
        )

        return (
            0 if is_ats_url(url) else 1 if applyish and not is_aggregator_url(url) else 2 if not is_aggregator_url(url) else 3,
            0 if "career" in host or "job" in host else 1,
            len(url),
        )

    return [
        {
            "url": item["url"],
            "method": "jooble_outbound",
            "confidence": 0.98 if is_ats_url(item["url"]) else 0.90,
        }
        for item in sorted(candidates, key=score)
        if not is_aggregator_url(item["url"])
    ][:8]


def _tokens(value):
    return {
        token
        for token in re.findall(r"[a-z0-9]+", str(value or "").casefold())
        if len(token) >= 2
        and token not in {
            "the",
            "and",
            "for",
            "with",
            "job",
            "jobs",
            "role",
            "career",
            "careers",
            "singapore",
            "sg",
            "pte",
            "ltd",
            "limited",
            "inc",
        }
    }


def _coverage(needle_tokens, haystack_tokens):
    if not needle_tokens:
        return 0.0
    return len(needle_tokens & haystack_tokens) / len(needle_tokens)


def _organic_candidate_score(job, result):
    url = str(result.get("link") or "").strip()
    if not url or is_aggregator_url(url):
        return None

    title = str(job.get("raw_title") or "")
    company = str(job.get("raw_company_name") or "")
    location = str(job.get("location_raw") or "")

    evidence = " ".join(
        [
            str(result.get("title") or ""),
            str(result.get("snippet") or ""),
            str(result.get("source") or ""),
            host_for_url(url).replace(".", " "),
        ]
    )

    evidence_tokens = _tokens(evidence)
    title_score = _coverage(_tokens(title), evidence_tokens)
    company_score = _coverage(_tokens(company), evidence_tokens)
    location_score = _coverage(_tokens(location), evidence_tokens)

    exact_title = (
        bool(title)
        and re.sub(r"\s+", " ", title.casefold()).strip()
        in re.sub(r"\s+", " ", evidence.casefold())
    )

    score = (
        0.55 * (1.0 if exact_title else title_score)
        + 0.30 * company_score
        + 0.05 * location_score
        + (0.10 if is_ats_url(url) else 0.0)
    )

    if "career" in host_for_url(url) or "job" in host_for_url(url):
        score += 0.05

    return min(score, 1.0)


def search_official_job_candidates(job):
    """Use one exact Google/SerpAPI lookup only when provider links cannot resolve.

    This is intentionally an on-demand fallback for Jooble results. It is not
    called while browsing/searching and successful resolution is persisted by
    the API layer so future opens can reuse the employer URL.
    """

    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return []

    title = str(job.get("raw_title") or "").strip()
    company = str(job.get("raw_company_name") or "").strip()
    location = str(job.get("location_raw") or "").strip()

    if not title or not company:
        return []

    query = f'"{title}" "{company}"'
    if location:
        query += f' "{location}"'
    query += " careers OR jobs"

    try:
        response = httpx.get(
            SERPAPI_SEARCH_URL,
            params={
                "engine": "google",
                "q": query,
                "gl": "sg",
                "hl": "en",
                "num": 10,
                "api_key": api_key,
            },
            timeout=SEARCH_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        print(
            "[CareerLens source resolver] "
            f"official-source search failed for job {job.get('job_id')}: {exc}",
            flush=True,
        )
        return []

    ranked = []
    for result in payload.get("organic_results") or []:
        if not isinstance(result, dict):
            continue

        score = _organic_candidate_score(job, result)
        if score is None or score < 0.58:
            continue

        url = str(result.get("link") or "").strip()
        if not url:
            continue

        ranked.append(
            {
                "url": url,
                "method": "serpapi_official_search",
                "confidence": round(score, 3),
                "search_title": str(result.get("title") or ""),
            }
        )

    ranked.sort(
        key=lambda item: (
            -item["confidence"],
            0 if is_ats_url(item["url"]) else 1,
            len(item["url"]),
        )
    )

    return ranked[:5]
