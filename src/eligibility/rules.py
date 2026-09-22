import re


EDUCATION_LEVELS = {
    "diploma": 1,
    "bachelor": 2,
    "master": 3,
    "phd": 4,
}


EDUCATION_PATTERNS = [
    (
        "phd",
        re.compile(
            r"\b(ph\.?d\.?|doctorate)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "master",
        re.compile(
            r"\bmaster'?s?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "bachelor",
        re.compile(
            r"\bbachelor'?s?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "diploma",
        re.compile(
            r"\bdiploma\b",
            re.IGNORECASE,
        ),
    ),
]


GRADUATION_RANGE_PATTERN = re.compile(
    r"\b(?:graduating|graduate|graduation)"
    r".{0,30}?"
    r"(20\d{2})"
    r"\s*(?:-|–|to|and)\s*"
    r"(20\d{2})\b",
    re.IGNORECASE,
)


GRADUATION_YEAR_PATTERN = re.compile(
    r"\b(?:graduating|graduate|graduation)"
    r".{0,30}?"
    r"(20\d{2})\b",
    re.IGNORECASE,
)


LANGUAGE_PATTERN = re.compile(
    r"\b(?:fluent|fluency)"
    r"\s+in\s+"
    r"([A-Za-z][A-Za-z ,/&-]+)",
    re.IGNORECASE,
)


YEAR_PATTERN = re.compile(
    r"\b(20\d{2})\b"
)


def extract_education_level(text):
    matches = []

    for level, pattern in EDUCATION_PATTERNS:
        if pattern.search(text):
            matches.append(
                (
                    EDUCATION_LEVELS[level],
                    level,
                )
            )

    if not matches:
        return None

    # If a posting says "Bachelor's or Master's",
    # Bachelor's is the minimum acceptable level.
    matches.sort(
        key=lambda item: item[0]
    )

    rank, level = matches[0]

    return {
        "level": level,
        "rank": rank,
    }


def extract_graduation_requirement(text):
    range_match = (
        GRADUATION_RANGE_PATTERN.search(
            text
        )
    )

    if range_match:
        return (
            "between",
            {
                "min_year": int(
                    range_match.group(1)
                ),
                "max_year": int(
                    range_match.group(2)
                ),
            },
        )

    year_match = (
        GRADUATION_YEAR_PATTERN.search(
            text
        )
    )

    if year_match:
        return (
            "eq",
            {
                "year": int(
                    year_match.group(1)
                )
            },
        )

    return None


def extract_languages(text):
    match = LANGUAGE_PATTERN.search(
        text
    )

    if not match:
        return []

    captured = match.group(1)

    parts = re.split(
        r"\s*(?:,|/|\band\b)\s*",
        captured,
        flags=re.IGNORECASE,
    )

    results = []

    for part in parts:
        language = part.strip(
            " .;:"
        )

        if not language:
            continue

        results.append(
            language.casefold()
        )

    return results


def extract_profile_graduation_year(text):
    years = [
        int(match.group(1))
        for match in YEAR_PATTERN.finditer(
            text
        )
    ]

    if not years:
        return None

    # Resume education dates are ambiguous.
    # Returning the latest year as a candidate,
    # not a confirmed fact.
    return max(years)