import html
import re


WHITESPACE_PATTERN = re.compile(
    r"\s+"
)


TRAILING_REQUIREMENT_PATTERN = re.compile(
    r"(?:\b(?:is|are)\s+)?\b("
    r"required|"
    r"preferred|"
    r"mandatory|"
    r"would be a plus|"
    r"is a plus|"
    r"is advantageous|"
    r"is an advantage|"
    r"an advantage|"
    r"will be an advantage"
    r")\b.*$",
    re.IGNORECASE,
)


LEADING_NOISE_PATTERN = re.compile(
    r"^(?:"
    r"and|"
    r"or|"
    r"as|"
    r"such as|"
    r"including|"
    r"including but not limited to|"
    r"experience with"
    r")\s+",
    re.IGNORECASE,
)


OPEN_HINT_PATTERN = re.compile(
    r"\b(?:"
    r"(?:related|relevant)\s+"
    r"(?:fields?|disciplines?)|"
    r"similar\s+(?:"
    r"fields?|"
    r"disciplines?|"
    r"tools?|"
    r"platforms?|"
    r"languages?"
    r")|"
    r"equivalent\s+(?:"
    r"tools?|"
    r"platforms?|"
    r"software|"
    r"visuali[sz]ation\s+tools?"
    r")|"
    r"other\s+.+?\s+(?:"
    r"tools?|"
    r"platforms?|"
    r"software|"
    r"languages?|"
    r"fields?|"
    r"disciplines?"
    r")|"
    r"(?:a\s+)?quantitative\s+disciplines?|"
    r"etc\.?"
    r")\b",
    re.IGNORECASE,
)


EXAMPLE_PATTERN = re.compile(
    r"\b("
    r"e\.?\s*g\.?|"
    r"such as|"
    r"including"
    r")\b",
    re.IGNORECASE,
)


EDUCATION_CAPTURE_PATTERN = re.compile(
    r"\b(?:"
    r"degree|"
    r"diploma"
    r")"
    r"\s+in\s*:?\s*(.+)",
    re.IGNORECASE,
)


LANGUAGE_CAPTURE_PATTERN = re.compile(
    r"\b(?:"
    r"fluent|"
    r"fluency"
    r")"
    r"\s+in\s+(.+)",
    re.IGNORECASE,
)


CERTIFICATION_CAPTURE_PATTERN = re.compile(
    r"\b(?:"
    r"certification|"
    r"certified"
    r")"
    r"(?:\s+in|\s+as)?"
    r"\s+(.+)",
    re.IGNORECASE,
)


STRONG_SKILLS_PATTERN = re.compile(
    r"\b(?:"
    r"strong|"
    r"excellent|"
    r"advanced"
    r")\s+"
    r"(.+?)\s+"
    r"(?:skills|capabilities)\b",
    re.IGNORECASE,
)


ABILITY_TO_USE_PATTERN = re.compile(
    r"\bability to use\s+(.+)",
    re.IGNORECASE,
)


ABILITY_PATTERN = re.compile(
    r"\bability to\s+(.+)",
    re.IGNORECASE,
)


ADVANCED_COMPETENCY_PATTERN = re.compile(
    r"\badvanced competency in\s+(.+)",
    re.IGNORECASE,
)


TOOL_LIST_ITEM_PATTERN = re.compile(
    r"^(?:"
    r"analytical software|"
    r"data visuali[sz]ation tools?|"
    r"a relational or graph database "
    r"management tool|"
    r"relational or graph database "
    r"management tool|"
    r"programming"
    r")\b",
    re.IGNORECASE,
)


GENERIC_CAPTURE_PATTERNS = [
    re.compile(
        r"\bproficiency in\s+(.+)",
        re.IGNORECASE,
    ),

    re.compile(
        r"\bproficient in\s+(.+)",
        re.IGNORECASE,
    ),

    re.compile(
        r"\bproficient with\s+(.+)",
        re.IGNORECASE,
    ),

    re.compile(
        r"\bexperience with\s+(.+)",
        re.IGNORECASE,
    ),

    re.compile(
        r"\bexperience using\s+(.+)",
        re.IGNORECASE,
    ),

    re.compile(
        r"\bfamiliarity with\s+(.+)",
        re.IGNORECASE,
    ),

    re.compile(
        r"\bfamiliar with\s+(.+)",
        re.IGNORECASE,
    ),

    re.compile(
        r"\bknowledge of\s+(.+)",
        re.IGNORECASE,
    ),

    re.compile(
        r"\bskills in\s+(.+)",
        re.IGNORECASE,
    ),
]


GENERIC_CONCEPTS = {
    "tool",
    "tools",
    "software",
    "platform",
    "platforms",
    "system",
    "systems",
    "service",
    "services",
    "framework",
    "frameworks",
    "skill",
    "skills",
    "capability",
    "capabilities",
    "related field",
    "related fields",
    "related discipline",
    "related disciplines",
    "relevant field",
    "relevant fields",
    "relevant discipline",
    "relevant disciplines",
    "similar tool",
    "similar tools",
    "equivalent tool",
    "equivalent tools",
}


CANONICAL_CONCEPT_ALIASES = {
    "microsoft excel": (
        "Excel",
        "excel",
    ),

    "ms excel": (
        "Excel",
        "excel",
    ),

    "microsoft power bi": (
        "Power BI",
        "power bi",
    ),

    "powerbi": (
        "Power BI",
        "power bi",
    ),

    "microsoft power automate": (
        "Power Automate",
        "power automate",
    ),
}


PROTECTED_AND_PATTERN = re.compile(
    r"^(?:"
    r"current\s+and\s+emerging|"
    r"new\s+and\s+emerging|"
    r"written\s+and\s+verbal|"
    r"verbal\s+and\s+written|"
    r"analytical\s+and\s+problem[- ]solving|"
    r"data\s+analysis\s+and\s+correlation"
    r")\b",
    re.IGNORECASE,
)


def normalize_concept(
    text,
):
    text = html.unescape(
        text
    )

    text = text.casefold()

    text = re.sub(
        r"[^a-z0-9+#.]+",
        " ",
        text,
    )

    text = WHITESPACE_PATTERN.sub(
        " ",
        text,
    )

    return text.strip()


def canonicalize_candidate(
    candidate,
):
    normalized = normalize_concept(
        candidate
    )

    canonical = (
        CANONICAL_CONCEPT_ALIASES.get(
            normalized
        )
    )

    if canonical is None:
        return (
            candidate,
            normalized,
        )

    return canonical


def clean_candidate(
    text,
):
    text = html.unescape(
        text
    )

    text = TRAILING_REQUIREMENT_PATTERN.sub(
        "",
        text,
    )

    # Preserve parentheses so concepts
    # such as:
    #
    # Large Language Models (LLMs)
    #
    # retain their full display name.
    text = text.strip(
        " \t.,:;-[]"
    )

    while LEADING_NOISE_PATTERN.search(
        text
    ):

        text = LEADING_NOISE_PATTERN.sub(
            "",
            text,
            count=1,
        )

    text = text.strip(
        " \t.,:;-[]"
    )

    text = WHITESPACE_PATTERN.sub(
        " ",
        text,
    )

    return text.strip()


def is_open_alternative(
    text,
):
    if not text:
        return False

    return bool(
        OPEN_HINT_PATTERN.search(
            text
        )
    )


def is_generic_open_candidate(
    text,
):
    normalized = normalize_concept(
        text
    )

    if not normalized:
        return False


    if re.fullmatch(
        r"(?:a\s+)?(?:related|relevant)\s+"
        r"(?:field|fields|discipline|disciplines)",
        normalized,
    ):
        return True


    if re.fullmatch(
        r"(?:a\s+)?similar\s+.+",
        normalized,
    ):
        return True


    if re.fullmatch(
        r"(?:an\s+)?equivalent\s+.+",
        normalized,
    ):
        return True


    if re.fullmatch(
        r"other\s+.+\s+"
        r"(?:"
        r"tool|tools|"
        r"platform|platforms|"
        r"software|"
        r"language|languages|"
        r"field|fields|"
        r"discipline|disciplines"
        r")(?:\s+is)?",
        normalized,
    ):
        return True


    if re.fullmatch(
        r"(?:a\s+)?quantitative\s+"
        r"(?:discipline|disciplines)",
        normalized,
    ):
        return True


    if normalized in {
        "etc",
        "etc.",
    }:
        return True


    return False


def extract_example_section(
    text,
):
    match = EXAMPLE_PATTERN.search(
        text
    )

    if match is None:
        return (
            text,
            False,
        )


    example_text = text[
        match.end():
    ]

    example_text = example_text.lstrip(
        " \t,:-("
    )


    # Remove only an outer example
    # wrapper.
    #
    # Example:
    #
    # e.g. Python, SQL, Excel)
    #
    # Parentheses inside concepts such
    # as (LLMs) and (RAG) are preserved.
    if (
        example_text.endswith(
            ")"
        )

        and
        example_text.count(
            "("
        )
        <
        example_text.count(
            ")"
        )
    ):

        example_text = (
            example_text[:-1]
        )


    return (
        example_text,
        True,
    )


def reduce_purpose_clause(
    text,
):
    # Example:
    #
    # Python for data analysis
    #
    # → Python
    match = re.match(
        r"^(.+?)\s+\bfor\b\s+"
        r"(?:data\s+)?"
        r"(?:"
        r"analysis|"
        r"analytics|"
        r"validation|"
        r"automation|"
        r"reporting"
        r")\b.*$",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1)


    # Example:
    #
    # SQL or Python to process and
    # analyze data
    #
    # → SQL or Python
    match = re.match(
        r"^(.+?)\s+\bto\b\s+"
        r"(?:"
        r"process|"
        r"analyse|"
        r"analyze|"
        r"validate|"
        r"automate|"
        r"transform"
        r")\b.*$",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1)


    return text


def determine_group_operator(
    text,
    requirement_type,
    is_example,
):
    if is_example:
        return "any_of"


    if (
        requirement_type
        == "education"

        and (
            "," in text

            or
            re.search(
                r"\s+\bor\b\s+",
                text,
                re.IGNORECASE,
            )
        )
    ):
        return "any_of"


    if re.search(
        r"\s+\bor\b\s+",
        text,
        flags=re.IGNORECASE,
    ):
        return "any_of"


    return "all_of"


def should_split_and(
    text,
):
    text = clean_candidate(
        text
    )

    if PROTECTED_AND_PATTERN.search(
        text
    ):
        return False


    return bool(
        re.search(
            r"\s+\band\b\s+",
            text,
            re.IGNORECASE,
        )
    )


def split_candidates(
    text,
    group_operator,
):
    text = clean_candidate(
        text
    )

    if not text:
        return []


    if group_operator == "any_of":

        parts = re.split(
            r"\s*(?:,|;|\bor\b)\s*",
            text,
            flags=re.IGNORECASE,
        )


    else:

        if (
            "," in text
            or ";" in text
        ):

            parts = re.split(
                r"\s*[,;]\s*",
                text,
            )

            expanded = []


            for index, part in enumerate(
                parts
            ):

                cleaned_part = (
                    clean_candidate(
                        part
                    )
                )


                # Typical:
                #
                # communication,
                # presentation,
                # project management
                # and time management
                #
                # Split the final pair,
                # while preserving
                # phrases such as:
                #
                # current and emerging
                # AI technologies
                if (
                    index
                    == len(parts) - 1

                    and
                    should_split_and(
                        cleaned_part
                    )
                ):

                    expanded.extend(
                        re.split(
                            r"\s+\band\b\s+",
                            cleaned_part,
                            flags=re.IGNORECASE,
                        )
                    )

                else:

                    expanded.append(
                        cleaned_part
                    )


            parts = expanded


        else:

            parts = [
                text
            ]


    result = []


    for part in parts:

        part = clean_candidate(
            part
        )

        if part:
            result.append(
                part
            )


    return result


def extract_capture(
    raw_text,
    requirement_type,
):
    if requirement_type == "education":

        match = EDUCATION_CAPTURE_PATTERN.search(
            raw_text
        )

        if match:
            return match.group(1)


    if requirement_type == "language":

        match = LANGUAGE_CAPTURE_PATTERN.search(
            raw_text
        )

        if match:
            return match.group(1)


    if requirement_type == "certification":

        match = CERTIFICATION_CAPTURE_PATTERN.search(
            raw_text
        )

        if match:
            return match.group(1)


    if requirement_type == "tool":

        match = ABILITY_TO_USE_PATTERN.search(
            raw_text
        )

        if match:
            return match.group(1)


        match = ADVANCED_COMPETENCY_PATTERN.search(
            raw_text
        )

        if match:
            return match.group(1)


        if TOOL_LIST_ITEM_PATTERN.search(
            raw_text
        ):
            return raw_text


    if requirement_type == "skill":

        match = STRONG_SKILLS_PATTERN.search(
            raw_text
        )

        if match:
            return match.group(1)


        match = ABILITY_PATTERN.search(
            raw_text
        )

        if match:
            return match.group(1)


    for pattern in GENERIC_CAPTURE_PATTERNS:

        match = pattern.search(
            raw_text
        )

        if match:
            return match.group(1)


    return None


def extract_atomic_concepts(
    raw_text,
    requirement_type,
):
    if not raw_text:
        return []


    capture = extract_capture(
        raw_text,
        requirement_type,
    )

    if capture is None:
        return []


    capture = clean_candidate(
        capture
    )

    if not capture:
        return []


    # Recover education lists where a
    # provider removed separators:
    #
    # Supply Chain ManagementIndustrial
    # EngineeringData Analytics...
    #
    # Restrict this to education so we
    # do not damage product/tool names.
    if requirement_type == "education":

        capture = re.sub(
            r"(?<=[a-z])(?=[A-Z])",
            ", ",
            capture,
        )


    capture = reduce_purpose_clause(
        capture
    )


    # Determine whether the requirement
    # is open before generic alternatives
    # are removed.
    group_is_open = (
        is_open_alternative(
            capture
        )
    )


    capture, is_example = (
        extract_example_section(
            capture
        )
    )


    if is_example:
        group_is_open = True


    group_operator = (
        determine_group_operator(
            capture,
            requirement_type,
            is_example,
        )
    )


    candidates = split_candidates(
        capture,
        group_operator,
    )


    results = []
    seen = set()


    for candidate in candidates:

        candidate = clean_candidate(
            candidate
        )

        if not candidate:
            continue


        if is_open_alternative(
            candidate
        ):
            group_is_open = True


        # Generic alternatives such as:
        #
        # related disciplines
        # relevant disciplines
        # equivalent visualization tools
        #
        # indicate an open group but
        # should not become requirements
        # themselves.
        if is_generic_open_candidate(
            candidate
        ):

            group_is_open = True
            continue


        candidate, normalized = (
            canonicalize_candidate(
                candidate
            )
        )


        if not normalized:
            continue


        if normalized in GENERIC_CONCEPTS:

            group_is_open = True
            continue


        if len(
            normalized.split()
        ) > 12:
            continue


        if len(normalized) < 2:

            raw_candidate = (
                candidate.strip()
            )

            if not (
                len(raw_candidate)
                == 1

                and
                raw_candidate.isalpha()

                and
                raw_candidate.isupper()
            ):
                continue


        if normalized in seen:
            continue


        seen.add(
            normalized
        )


        results.append(
            {
                "raw_text":
                    candidate,

                "normalized_key":
                    normalized,

                "group_operator":
                    group_operator,

                "group_is_open":
                    False,
            }
        )


    # Openness may only become known
    # after examining a later candidate.
    #
    # Apply the final state to every
    # surviving concept in the group.
    for result in results:

        result[
            "group_is_open"
        ] = group_is_open


    return results
