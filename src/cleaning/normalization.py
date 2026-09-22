import html
import json
import re

from datetime import timedelta


WHITESPACE_PATTERN = re.compile(r"\s+")

HTML_TAG_PATTERN = re.compile(
    r"<[^>]+>"
)

PUNCTUATION_PATTERN = re.compile(
    r"[^a-z0-9]+"
)


LEGAL_SUFFIX_PATTERN = re.compile(
    r"\b("
    r"pte\s+ltd|"
    r"private\s+limited|"
    r"limited|"
    r"ltd|"
    r"incorporated|"
    r"inc|"
    r"llc|"
    r"corporation|"
    r"corp"
    r")\b",
    re.IGNORECASE,
)


SEASON_YEAR_PATTERNS = [
    re.compile(
        r"\b("
        r"spring|summer|fall|autumn|winter"
        r")\s*(20\d{2})\b",
        re.IGNORECASE,
    ),

    re.compile(
        r"\b(20\d{2})\s*("
        r"spring|summer|fall|autumn|winter"
        r")\b",
        re.IGNORECASE,
    ),
]


def collapse_whitespace(value):
    if value is None:
        return None

    value = WHITESPACE_PATTERN.sub(
        " ",
        value,
    )

    return value.strip()


def strip_html(value):
    if not value:
        return None

    value = html.unescape(value)

    value = HTML_TAG_PATTERN.sub(
        " ",
        value,
    )

    return collapse_whitespace(
        value
    )


def normalize_basic(value):
    if not value:
        return None

    value = html.unescape(value)

    value = value.casefold()

    value = value.replace(
        "&",
        " and ",
    )

    value = PUNCTUATION_PATTERN.sub(
        " ",
        value,
    )

    return collapse_whitespace(
        value
    )


def normalize_title(title):
    return normalize_basic(title)


def normalize_company_name(company):
    company = normalize_basic(
        company
    )

    if not company:
        return None

    company = LEGAL_SUFFIX_PATTERN.sub(
        " ",
        company,
    )

    return collapse_whitespace(
        company
    )


def normalize_location(location):
    location = normalize_basic(
        location
    )

    if not location:
        return None

    # Common provider variation.
    if location in {
        "singapore singapore",
        "singapore",
    }:
        return "singapore"

    return location


def normalize_description(description):
    return strip_html(
        description
    )


def get_metadata(value):
    if value is None:
        return {}

    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            return json.loads(value)

        except json.JSONDecodeError:
            return {}

    return {}


def extract_recruiting_cycle_years(
    title,
):
    if not title:
        return []

    years = []

    for pattern in SEASON_YEAR_PATTERNS:
        for match in pattern.finditer(
            title
        ):
            groups = match.groups()

            for value in groups:
                if (
                    value
                    and value.isdigit()
                ):
                    years.append(
                        int(value)
                    )

    return sorted(
        set(years)
    )


def derive_posted_date(
    source_date,
    source_metadata,
    first_seen_at,
):
    if source_date is not None:
        return (
            source_date,
            "source_date",
        )

    if first_seen_at is None:
        return None, None

    metadata = get_metadata(
        source_metadata
    )

    posted_at = metadata.get(
        "posted_at"
    )

    if not posted_at:
        return None, None

    posted_at = (
        str(posted_at)
        .strip()
        .casefold()
    )

    observation_date = (
        first_seen_at.date()
    )


    if posted_at in {
        "today",
        "just posted",
    }:
        return (
            observation_date,
            "provider_relative_today",
        )


    if posted_at == "yesterday":
        return (
            observation_date
            - timedelta(days=1),

            "provider_relative_days",
        )


    hours_match = re.fullmatch(
        r"(\d+)\s+hours?\s+ago",
        posted_at,
    )

    if hours_match:
        hours = int(
            hours_match.group(1)
        )

        days = hours // 24

        return (
            observation_date
            - timedelta(days=days),

            "provider_relative_hours",
        )


    days_match = re.fullmatch(
        r"(\d+)\s+days?\s+ago",
        posted_at,
    )

    if days_match:
        days = int(
            days_match.group(1)
        )

        return (
            observation_date
            - timedelta(days=days),

            "provider_relative_days",
        )


    weeks_match = re.fullmatch(
        r"(\d+)\s+weeks?\s+ago",
        posted_at,
    )

    if weeks_match:
        weeks = int(
            weeks_match.group(1)
        )

        return (
            observation_date
            - timedelta(days=weeks * 7),

            "provider_relative_weeks",
        )


    # Do not invent an exact date for things
    # such as "30+ days ago" or "1 month ago".
    return None, None


def relative_age_days(
    source_metadata,
):
    metadata = get_metadata(
        source_metadata
    )

    posted_at = metadata.get(
        "posted_at"
    )

    if not posted_at:
        return None

    posted_at = (
        str(posted_at)
        .strip()
        .casefold()
    )


    if posted_at in {
        "today",
        "just posted",
    }:
        return 0


    if posted_at == "yesterday":
        return 1


    hours_match = re.fullmatch(
        r"(\d+)\s+hours?\s+ago",
        posted_at,
    )

    if hours_match:
        return 0


    days_match = re.fullmatch(
        r"(\d+)\s+days?\s+ago",
        posted_at,
    )

    if days_match:
        return int(
            days_match.group(1)
        )


    weeks_match = re.fullmatch(
        r"(\d+)\s+weeks?\s+ago",
        posted_at,
    )

    if weeks_match:
        return (
            int(
                weeks_match.group(1)
            )
            * 7
        )


    return None