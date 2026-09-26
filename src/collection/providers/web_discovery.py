import hashlib
import re
from urllib.parse import urlparse, urlunparse

import requests

from src.collection.models import NormalizedJob, ProviderPage
from src.services.manual_job_service import JobPageFetchError, fetch_job_listing


SERPAPI_URL = "https://serpapi.com/search.json"
MIN_ANALYSABLE_DESCRIPTION_CHARS = 1000
MAX_ORGANIC_RESULTS = 10

GENERIC_PATH_MARKERS = {
    "/jobs",
    "/job-search",
    "/search",
    "/careers",
    "/career",
}

NON_JOB_HOSTS = {
    "facebook.com",
    "www.facebook.com",
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "instagram.com",
    "www.instagram.com",
    "reddit.com",
    "www.reddit.com",
}

ROLE_STOPWORDS = {
    "a",
    "an",
    "and",
    "at",
    "for",
    "in",
    "of",
    "on",
    "the",
}

ROLE_EQUIVALENTS = {
    "engineering": "engineer",
    "developer": "engineer",
    "development": "engineer",
    "trading": "trader",
    "quant": "quantitative",
}

SENIORITY_TERMS = {
    "senior",
    "sr",
    "lead",
    "principal",
    "staff",
    "manager",
    "director",
    "head",
}

EARLY_CAREER_TERMS = {
    "intern",
    "internship",
    "graduate",
    "campus",
    "student",
    "trainee",
}


def _normalise_space(value):
    return re.sub(r"\s+", " ", value or "").strip()


def _normalise_role_token(token):
    token = token.lower().strip("-_/.,()[]{}")
    return ROLE_EQUIVALENTS.get(token, token)


def _role_tokens(value):
    return {
        _normalise_role_token(token)
        for token in re.findall(r"[a-zA-Z0-9+#.-]+", value or "")
        if _normalise_role_token(token)
        and _normalise_role_token(token) not in ROLE_STOPWORDS
    }


def _canonical_url(url):
    parsed = urlparse(url)
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/") or "/",
            "",
            "",
            "",
        )
    )


def _looks_like_generic_page(url, title):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path.rstrip("/").lower() or "/"
    title_lower = (title or "").lower()

    if host in NON_JOB_HOSTS:
        return True

    generic_title_patterns = (
        r"\b\d+[+,]?\s+.*\bjobs?\b",
        r"\bjobs?\s+in\b",
        r"\bsearch\s+.*\bjobs?\b",
        r"\bfind\s+.*\bjobs?\b",
    )

    if any(re.search(pattern, title_lower) for pattern in generic_title_patterns):
        return True

    if path in GENERIC_PATH_MARKERS:
        return True

    if "linkedin." in host and "/jobs/view/" not in path:
        return True

    if "indeed." in host and "/viewjob" not in path:
        return True

    if "glassdoor." in host and "/job-listing/" not in path:
        return True

    if "jobstreet." in host and "/job/" not in path:
        return True

    return False


def _title_relevance(query, title):
    query_tokens = _role_tokens(query)
    title_tokens = _role_tokens(title)

    if not query_tokens or not title_tokens:
        return 0.0

    overlap = len(query_tokens & title_tokens) / len(query_tokens)

    query_early = bool(query_tokens & EARLY_CAREER_TERMS)
    title_early = bool(title_tokens & EARLY_CAREER_TERMS)
    title_senior = bool(title_tokens & SENIORITY_TERMS)

    if query_early and title_senior and not title_early:
        return 0.0

    if query_early and not title_early:
        overlap *= 0.65

    return overlap


def _location_matches(location, *values):
    requested = _normalise_space(location).lower()

    if not requested:
        return True

    combined = " ".join(
        _normalise_space(value).lower()
        for value in values
        if value
    )

    return requested in combined


def _targeted_query(query, location):
    return (
        f'"{query.strip()}" "{location.strip()}" '
        '("responsibilities" OR "requirements" OR '
        '"qualifications" OR "what you will do")'
    )


def search_web_discovery(
    query,
    location,
    country_code,
    api_key,
):
    search_query = _targeted_query(query, location)

    params = {
        "engine": "google",
        "q": search_query,
        "gl": country_code.lower(),
        "hl": "en",
        "num": MAX_ORGANIC_RESULTS,
        "api_key": api_key,
    }

    response = requests.get(
        SERPAPI_URL,
        params=params,
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()

    jobs = []
    seen_urls = set()

    for result in payload.get("organic_results", [])[:MAX_ORGANIC_RESULTS]:
        url = _normalise_space(result.get("link"))
        search_title = _normalise_space(result.get("title"))
        snippet = _normalise_space(result.get("snippet"))

        if not url or not search_title:
            continue

        canonical_url = _canonical_url(url)
        if canonical_url in seen_urls:
            continue
        seen_urls.add(canonical_url)

        if _looks_like_generic_page(url, search_title):
            continue

        search_relevance = _title_relevance(query, search_title)
        if search_relevance < 0.60:
            continue

        if not _location_matches(location, search_title, snippet):
            continue

        try:
            listing = fetch_job_listing(url)
        except JobPageFetchError:
            continue
        except Exception:
            continue

        listing_title = _normalise_space(listing.get("title")) or search_title
        listing_company = _normalise_space(listing.get("company")) or "Unknown Company"
        listing_location = _normalise_space(listing.get("location"))
        description = _normalise_space(listing.get("description"))
        final_url = _normalise_space(listing.get("url")) or url

        actual_relevance = _title_relevance(query, listing_title)
        if actual_relevance < 0.60:
            continue

        if not _location_matches(
            location,
            listing_location,
            listing_title,
            description[:1500],
            snippet,
        ):
            continue

        if len(description) < MIN_ANALYSABLE_DESCRIPTION_CHARS:
            continue

        source_job_id = hashlib.sha256(
            _canonical_url(final_url).encode("utf-8")
        ).hexdigest()[:32]

        jobs.append(
            NormalizedJob(
                source="SerpApi Web Discovery",
                source_job_id=source_job_id,
                job_url=final_url,
                title=listing_title,
                company_name=listing_company,
                location_raw=listing_location or location,
                location_country=(
                    "Singapore"
                    if country_code.lower() == "sg"
                    else country_code.upper()
                ),
                employment_type=listing.get("employment_type"),
                salary_text=None,
                description=description,
                date_posted=None,
                metadata={
                    "discovery_query": search_query,
                    "search_result_title": search_title,
                    "search_result_snippet": snippet,
                    "search_title_relevance": round(search_relevance, 4),
                    "listing_title_relevance": round(actual_relevance, 4),
                    "extraction_method": listing.get("extraction_method"),
                    "description_characters": len(description),
                    "directly_analysable": True,
                },
            )
        )

    yield ProviderPage(
        page_number=1,
        payload=payload,
        jobs=jobs,
        reported_count=len(payload.get("organic_results", [])),
    )
