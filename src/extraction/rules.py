import html
import re

from src.extraction.models import (
    RequirementMention,
)

from src.extraction.sections import (
    infer_level_from_section,
    split_job_sections,
)

from src.taxonomy.skill_classifier import (
    find_hard_skills,
    find_soft_skills,
)


WHITESPACE_PATTERN = re.compile(
    r"\s+"
)


SENTENCE_SPLIT_PATTERN = re.compile(
    r"(?<=[.!?;])\s+|\n+"
)


PREFERRED_PATTERN = re.compile(
    r"\b("
    r"preferred|"
    r"nice to have|"
    r"advantageous|"
    r"an advantage|"
    r"would be a plus|"
    r"is a plus|"
    r"strong plus|"
    r"desirable|"
    r"ideally|"
    r"bonus|"
    r"beneficial|"
    r"good to have"
    r")\b",
    re.IGNORECASE,
)


REQUIRED_PATTERN = re.compile(
    r"\b("
    r"must|"
    r"required|"
    r"mandatory|"
    r"minimum|"
    r"need to|"
    r"needs to|"
    r"essential|"
    r"prerequisite|"
    r"must have|"
    r"must-have|"
    r"you will need|"
    r"we require"
    r")\b",
    re.IGNORECASE,
)


EXPERIENCE_RANGE_PATTERN = re.compile(
    r"\b(\d+)\s*"
    r"(?:-|–|to)\s*"
    r"(\d+)\+?\s*"
    r"(?:years?|yrs?)\b",
    re.IGNORECASE,
)


EXPERIENCE_PATTERN = re.compile(
    r"\b(\d+)\+?\s*"
    r"(?:years?|yrs?)"
    r"(?:\s+of)?"
    r"(?:\s+[a-zA-Z-]+){0,4}"
    r"\s+experience\b",
    re.IGNORECASE,
)


DEMONSTRATED_EXPERIENCE_PATTERN = re.compile(
    r"\bdemonstrated experience\b",
    re.IGNORECASE,
)


EDUCATION_PATTERN = re.compile(
    r"\b("
    r"bachelor'?s?|"
    r"master'?s?|"
    r"ph\.?d\.?|"
    r"doctorate|"
    r"diploma|"
    r"degree|"
    r"undergraduate|"
    r"graduate"
    r")\b",
    re.IGNORECASE,
)


CERTIFICATION_PATTERN = re.compile(
    r"\b("
    r"certification|"
    r"certified|"
    r"certificate"
    r")\b",
    re.IGNORECASE,
)


NON_REQUIREMENT_CERTIFICATION_PATTERN = re.compile(
    r"\b("
    r"top employer|"
    r"companies certified|"
    r"company certified|"
    r"organisation certified|"
    r"organization certified|"
    r"employer certified"
    r")\b",
    re.IGNORECASE,
)


LICENCE_PATTERN = re.compile(
    r"\b("
    r"licence|"
    r"license|"
    r"licensed"
    r")\b",
    re.IGNORECASE,
)


PROFESSIONAL_REGISTRATION_PATTERN = re.compile(
    r"\b("
    r"professional registration|"
    r"registered with|"
    r"registration with|"
    r"registered as|"
    r"registration as|"
    r"admitted to practice|"
    r"admission to practice"
    r")\b",
    re.IGNORECASE,
)


LANGUAGE_PATTERN = re.compile(
    r"\b("
    r"fluent in|"
    r"fluency in|"
    r"language proficiency|"
    r"written and spoken|"
    r"spoken and written"
    r")\b",
    re.IGNORECASE,
)


WORK_AUTH_PATTERN = re.compile(
    r"\b("
    r"work authorization|"
    r"authorised to work|"
    r"authorized to work|"
    r"eligible to work|"
    r"work eligibility|"
    r"visa sponsorship|"
    r"permanent resident|"
    r"citizenship"
    r")\b",
    re.IGNORECASE,
)


AVAILABILITY_PATTERN = re.compile(
    r"\b("
    r"full[- ]time commitment|"
    r"part[- ]time commitment|"
    r"available for|"
    r"availability|"
    r"internship period|"
    r"commit for|"
    r"commit minimum|"
    r"start date|"
    r"full[- ]time interns?|"
    r"part[- ]time interns?"
    r")\b",
    re.IGNORECASE,
)


SECURITY_CLEARANCE_PATTERN = re.compile(
    r"\b("
    r"security clearance|"
    r"clearance required|"
    r"background clearance"
    r")\b",
    re.IGNORECASE,
)


PHYSICAL_REQUIREMENT_PATTERN = re.compile(
    r"\b("
    r"physical ability|"
    r"physically able|"
    r"manual handling|"
    r"able to lift|"
    r"ability to lift|"
    r"stand for extended|"
    r"standing for extended"
    r")\b",
    re.IGNORECASE,
)


TOOL_PATTERN = re.compile(
    r"\b(?:"
    r"proficient with|"
    r"experience using|"
    r"ability to use|"
    r"software such as|"
    r"tools? such as|"
    r"platforms? such as|"
    r"systems? such as|"
    r"services? such as|"
    r"frameworks? such as|"
    r"advanced competency in|"
    r"analytical software|"
    r"data visuali[sz]ation tools?|"
    r"database management tool|"
    r"relational or graph database|"
    r"programming\s*\(?e\.g\."
    r")",
    re.IGNORECASE,
)


DOMAIN_KNOWLEDGE_PATTERN = re.compile(
    r"\b("
    r"domain knowledge|"
    r"industry knowledge|"
    r"knowledge of .* regulations|"
    r"knowledge of .* standards|"
    r"knowledge of .* law|"
    r"understanding of .* regulations|"
    r"understanding of .* standards"
    r")\b",
    re.IGNORECASE,
)


SKILL_PATTERN = re.compile(
    r"\b("
    r"proficient in|"
    r"proficiency in|"
    r"experience with|"
    r"experience in|"
    r"expertise in|"
    r"expertise with|"
    r"knowledge of|"
    r"working knowledge of|"
    r"basic knowledge of|"
    r"understanding of|"
    r"strong command of|"
    r"command of|"
    r"competency in|"
    r"competence in|"
    r"track record in|"
    r"background in|"
    r"familiar with|"
    r"familiarity with|"
    r"skills in|"
    r"hands[- ]on experience|"
    r"strong .* skills|"
    r"excellent .* skills|"
    r"advanced .* skills|"
    r"strong .* capabilities|"
    r"excellent .* capabilities|"
    r"ability to"
    r")\b",
    re.IGNORECASE,
)


NAMED_SKILL_REQUIREMENT_PATTERN = re.compile(
    r"\b"
    r"([a-zA-Z][a-zA-Z &/\-]{1,60})"
    r"\s+skills?\s+"
    r"(?:are\s+|is\s+)?"
    r"(?:required|essential|preferred|desirable|important|necessary)"
    r"\b",
    re.IGNORECASE,
)


REVERSE_SKILL_EXPERIENCE_PATTERN = re.compile(
    r"^(?!\d+\s*(?:years?|yrs?)\b)"
    r"(.{2,80}?)\s+experience\b",
    re.IGNORECASE,
)


GENERAL_REQUIREMENT_PATTERN = re.compile(
    r"\b("
    r"must|"
    r"required|"
    r"preferred|"
    r"minimum|"
    r"qualification|"
    r"qualifications|"
    r"candidate should|"
    r"you should|"
    r"we are looking for"
    r")\b",
    re.IGNORECASE,
)


HEADING_PATTERN = re.compile(
    r"\b("
    r"mandatory requirements|"
    r"preferred experience|"
    r"desirable qualifications "
    r"(?:&|and) competencies|"
    r"technical skills|"
    r"soft skills|"
    r"experience & qualifications|"
    r"experience and qualifications|"
    r"qualifications education|"
    r"requirements|"
    r"qualifications"
    r")\s*:?\s*",
    re.IGNORECASE,
)


NO_SPACE_SENTENCE_BOUNDARY = re.compile(
    r"(?<=[.!?;])(?=[A-Z])"
)


REQUIREMENT_START_CUE = (
    r"(?:"
    r"Currently pursuing|"
    r"Pursuing|"
    r"Minimum(?:\s+\d+)?|"
    r"Demonstrated experience|"
    r"Strong|"
    r"Excellent|"
    r"Advanced competency|"
    r"Advanced|"
    r"Ability to|"
    r"Proficiency in|"
    r"Proficient in|"
    r"Proficient with|"
    r"Experience with|"
    r"Experience in|"
    r"Experience using|"
    r"Expertise in|"
    r"Expertise with|"
    r"Familiarity with|"
    r"Familiar with|"
    r"Knowledge of|"
    r"Working knowledge of|"
    r"Understanding of|"
    r"Strong command of|"
    r"Competency in|"
    r"Track record in|"
    r"Background in|"
    r"Basic knowledge of|"
    r"A desire and ability|"
    r"Enthusiasm and drive|"
    r"Full[- ]time interns?|"
    r"Part[- ]time interns?"
    r")"
)


GLUED_REQUIREMENT_BOUNDARY = re.compile(
    r"(?<=[a-z0-9)])"
    r"(?="
    + REQUIREMENT_START_CUE
    + r"\b)"
)


SPACED_REQUIREMENT_BOUNDARY = re.compile(
    r"\s+"
    r"(?="
    + REQUIREMENT_START_CUE
    + r"\b)"
)


EG_PLACEHOLDER = (
    "__CAREERLENS_EG__"
)


IE_PLACEHOLDER = (
    "__CAREERLENS_IE__"
)


def normalize_requirement_text(
    text,
):
    text = html.unescape(
        text
    )

    text = text.casefold()

    text = WHITESPACE_PATTERN.sub(
        " ",
        text,
    )

    return text.strip()


def prepare_requirement_text(
    text,
):
    text = html.unescape(
        text
    )


    for bullet in [
        "•",
        "●",
        "▪",
        "◦",
        "·",
    ]:

        text = text.replace(
            bullet,
            "\n",
        )


    # Protect abbreviations before
    # sentence splitting.
    #
    # Otherwise:
    #
    # (e.g. Python, SQL)
    #
    # may incorrectly split after
    # "e.g."
    text = re.sub(
        r"\be\.g\.",
        EG_PLACEHOLDER,
        text,
        flags=re.IGNORECASE,
    )


    text = re.sub(
        r"\bi\.e\.",
        IE_PLACEHOLDER,
        text,
        flags=re.IGNORECASE,
    )


    # Some job descriptions place the
    # example for a requirement on the
    # next physical line:
    #
    # database management tool
    # (e.g. SQL, NoSQL, Neo4J)
    #
    # Keep that example attached to the
    # preceding requirement.
    text = re.sub(
        r"\n\s*(?=\(\s*"
        + re.escape(
            EG_PLACEHOLDER
        )
        + r")",
        " ",
        text,
    )


    text = re.sub(
        r"\n\s*(?=\(\s*"
        + re.escape(
            IE_PLACEHOLDER
        )
        + r")",
        " ",
        text,
    )


    # Example:
    #
    # Programming. (e.g. Python...)
    #
    # The full stop is formatting, not
    # the end of the requirement.
    text = re.sub(
        r"\bProgramming\.\s*"
        r"(?=\(\s*"
        + re.escape(
            EG_PLACEHOLDER
        )
        + r")",
        "Programming ",
        text,
        flags=re.IGNORECASE,
    )


    # Example:
    #
    # data analysis.Experience with...
    text = NO_SPACE_SENTENCE_BOUNDARY.sub(
        "\n",
        text,
    )


    # Example:
    #
    # internshipPursuing Bachelor's...
    text = GLUED_REQUIREMENT_BOUNDARY.sub(
        "\n",
        text,
    )


    # Example where provider formatting
    # removes a list boundary but keeps
    # a space:
    #
    # relevant disciplines Excellent
    # communication skills
    text = SPACED_REQUIREMENT_BOUNDARY.sub(
        "\n",
        text,
    )


    text = HEADING_PATTERN.sub(
        lambda match:
            (
                "\n"
                + match.group(1)
                + "\n"
            ),
        text,
    )


    return text


def restore_abbreviations(
    text,
):
    text = text.replace(
        EG_PLACEHOLDER,
        "e.g.",
    )

    text = text.replace(
        IE_PLACEHOLDER,
        "i.e.",
    )

    return text


def split_requirement_units(
    text,
):
    if not text:
        return []


    text = prepare_requirement_text(
        text
    )


    units = []


    for unit in SENTENCE_SPLIT_PATTERN.split(
        text
    ):

        unit = restore_abbreviations(
            unit
        )

        unit = WHITESPACE_PATTERN.sub(
            " ",
            unit,
        ).strip(
            " -:\t"
        )


        # Short bullets are common in real job listings:
        # "SQL", "Excel", "Python", "Communication", etc.
        # Do not discard them before the skill extractor sees them.
        if len(
            unit.split()
        ) < 1:
            continue


        if HEADING_PATTERN.fullmatch(
            unit
        ):
            continue


        units.append(
            unit
        )


    return units


def detect_requirement_level(
    text,
):
    if PREFERRED_PATTERN.search(
        text
    ):
        return "preferred"


    if REQUIRED_PATTERN.search(
        text
    ):
        return "required"


    return "unknown"


def create_mention(
    requirement_type,
    text,
    level,
    rule_name,
    structured_value=None,
    section=None,
):
    metadata = {}

    if section is not None:
        metadata.update(
            section.metadata()
        )

    if structured_value:
        metadata.update(
            structured_value
        )

    return RequirementMention(
        requirement_type=
            requirement_type,

        raw_text=
            text,

        normalized_text=
            normalize_requirement_text(
                text
            ),

        requirement_level=
            level,

        rule_name=
            rule_name,

        structured_value=
            metadata,
    )


def _extract_unit_mentions(
    unit,
    section,
):
    mentions = []

    explicit_level = (
        detect_requirement_level(
            unit
        )
    )

    level = infer_level_from_section(
        section.section_type,
        explicit_level,
    )

    matched = False

    range_match = (
        EXPERIENCE_RANGE_PATTERN.search(
            unit
        )
    )

    if range_match:
        mentions.append(
            create_mention(
                "experience",
                unit,
                level,
                "experience_range",
                {
                    "min_years": int(
                        range_match.group(1)
                    ),
                    "max_years": int(
                        range_match.group(2)
                    ),
                },
                section=section,
            )
        )
        matched = True

    else:
        experience_match = (
            EXPERIENCE_PATTERN.search(
                unit
            )
        )

        if experience_match:
            mentions.append(
                create_mention(
                    "experience",
                    unit,
                    level,
                    "experience_years",
                    {
                        "min_years": int(
                            experience_match.group(1)
                        )
                    },
                    section=section,
                )
            )
            matched = True

        elif DEMONSTRATED_EXPERIENCE_PATTERN.search(
            unit
        ):
            mentions.append(
                create_mention(
                    "experience",
                    unit,
                    level,
                    "demonstrated_experience",
                    section=section,
                )
            )
            matched = True

    category_patterns = [
        (
            "education",
            EDUCATION_PATTERN,
            "education_keyword",
        ),
        (
            "professional_registration",
            PROFESSIONAL_REGISTRATION_PATTERN,
            "professional_registration_keyword",
        ),
        (
            "licence",
            LICENCE_PATTERN,
            "licence_keyword",
        ),
        (
            "language",
            LANGUAGE_PATTERN,
            "language_keyword",
        ),
        (
            "work_authorization",
            WORK_AUTH_PATTERN,
            "work_authorization_keyword",
        ),
        (
            "availability",
            AVAILABILITY_PATTERN,
            "availability_keyword",
        ),
        (
            "security_clearance",
            SECURITY_CLEARANCE_PATTERN,
            "security_clearance_keyword",
        ),
        (
            "physical_requirement",
            PHYSICAL_REQUIREMENT_PATTERN,
            "physical_requirement_keyword",
        ),
    ]

    for (
        requirement_type,
        pattern,
        rule_name,
    ) in category_patterns:
        if pattern.search(unit):
            mentions.append(
                create_mention(
                    requirement_type,
                    unit,
                    level,
                    rule_name,
                    section=section,
                )
            )
            matched = True

    if (
        CERTIFICATION_PATTERN.search(unit)
        and not NON_REQUIREMENT_CERTIFICATION_PATTERN.search(unit)
    ):
        mentions.append(
            create_mention(
                "certification",
                unit,
                level,
                "certification_keyword",
                section=section,
            )
        )
        matched = True

    if TOOL_PATTERN.search(unit):
        mentions.append(
            create_mention(
                "tool",
                unit,
                level,
                "tool_requirement_cue",
                section=section,
            )
        )
        matched = True

    elif DOMAIN_KNOWLEDGE_PATTERN.search(unit):
        mentions.append(
            create_mention(
                "domain_knowledge",
                unit,
                level,
                "domain_knowledge_cue",
                section=section,
            )
        )
        matched = True

    elif SKILL_PATTERN.search(unit):
        mentions.append(
            create_mention(
                "skill",
                unit,
                level,
                "skill_requirement_cue",
                section=section,
            )
        )
        matched = True

    elif NAMED_SKILL_REQUIREMENT_PATTERN.search(unit):
        mentions.append(
            create_mention(
                "skill",
                unit,
                level,
                "named_skill_requirement",
                section=section,
            )
        )
        matched = True

    # Named tools and canonical soft skills may be presented as very short
    # bullets with no cue phrase at all (e.g. "SQL", "Excel",
    # "Stakeholder management"). Preserve those units as skill mentions.
    if (
        not matched
        and (
            find_hard_skills(unit)
            or find_soft_skills(unit)
        )
    ):
        mentions.append(
            create_mention(
                "skill",
                unit,
                level,
                "direct_named_skill",
                section=section,
            )
        )
        matched = True

    # The reverse "X experience" rule is intentionally limited to candidate-
    # focused sections. In company/role prose, phrases such as "customer
    # experience" are usually not requirements and were a major source of
    # false-positive skills.
    elif (
        section.section_type
        in {"requirements", "preferred"}
        and REVERSE_SKILL_EXPERIENCE_PATTERN.search(unit)
    ):
        mentions.append(
            create_mention(
                "skill",
                unit,
                level,
                "reverse_experience_skill_cue",
                section=section,
            )
        )
        matched = True

    # Responsibilities are still valuable evidence, particularly for tools and
    # soft skills. Retain action-oriented statements as low-weight skill
    # candidates; the atomic extractor performs the actual skill filtering.
    if (
        not matched
        and section.section_type == "responsibilities"
        and re.match(
            r"^(?:build|create|develop|prepare|perform|conduct|analyse|analyze|model|use|manage|lead|present|communicate|collaborate|partner|negotiate|design|implement|maintain|research|forecast)\b",
            unit,
            re.IGNORECASE,
        )
    ):
        mentions.append(
            create_mention(
                "skill",
                unit,
                level,
                "responsibility_action_skill",
                section=section,
            )
        )
        matched = True

    if (
        not matched
        and GENERAL_REQUIREMENT_PATTERN.search(unit)
    ):
        mentions.append(
            create_mention(
                "other",
                unit,
                level,
                "general_requirement_cue",
                section=section,
            )
        )

    return mentions


def extract_requirements(
    text,
    source_field=None,
):
    if not text:
        return []

    mentions = []

    sections = split_job_sections(
        text,
        source_field=source_field,
    )

    for section in sections:
        # Company marketing copy, benefits, application instructions and legal
        # boilerplate should not contribute skills or requirements. This is the
        # main precision safeguard introduced by the section-aware extractor.
        if section.is_ignored:
            continue

        for unit in split_requirement_units(
            section.text
        ):
            mentions.extend(
                _extract_unit_mentions(
                    unit,
                    section,
                )
            )

    # Section detection should improve precision, never turn a valid listing
    # into an empty analysis. If no section produced any requirement at all,
    # fall back to a neutral whole-listing pass using the same extraction
    # rules. This keeps CareerLens functional for unusual provider formatting.
    if not mentions:
        from src.extraction.sections import JobSection

        fallback_section = JobSection(
            section_type="other",
            heading=None,
            text=text,
        )

        for unit in split_requirement_units(
            text
        ):
            mentions.extend(
                _extract_unit_mentions(
                    unit,
                    fallback_section,
                )
            )

    unique_mentions = {}

    for mention in mentions:
        key = (
            mention.requirement_type,
            mention.normalized_text,
        )

        existing = unique_mentions.get(key)

        if existing is None:
            unique_mentions[key] = mention
            continue

        # If the same sentence appears in multiple source sections, retain the
        # higher-priority interpretation. Required > preferred > unknown.
        strength = {
            "unknown": 0,
            "preferred": 1,
            "required": 2,
        }

        if strength.get(mention.requirement_level, 0) > strength.get(
            existing.requirement_level,
            0,
        ):
            unique_mentions[key] = mention

    return list(
        unique_mentions.values()
    )
