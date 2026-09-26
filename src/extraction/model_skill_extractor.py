import json
import logging
import os
import urllib.error
import urllib.request
from collections import defaultdict

from src.extraction.models import RequirementMention
from src.extraction.rules import normalize_requirement_text
from src.extraction.sections import (
    JobSection,
    infer_level_from_section,
    split_job_sections,
)


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.6-luna"
MAX_SECTION_CHARACTERS = 24000

ELIGIBLE_SECTION_TYPES = {
    "requirements",
    "preferred",
    "responsibilities",
    "role",
    "other",
}

logger = logging.getLogger(__name__)


TRUE_VALUES = {
    "1",
    "true",
    "yes",
    "on",
}


SYSTEM_INSTRUCTIONS = """You extract job-relevant skills from job advertisements for a career-matching product.

Return only skills and candidate eligibility/prerequisite requirements that are directly supported by the supplied candidate-focused sections. The product is occupation-agnostic, so recognize finance, business, software, data, engineering, marketing, HR, operations, legal, risk, sales and other professional skills.

A hard skill is a tool, software product, programming language, technical method, analytical technique, professional/domain competency, process/framework, regulatory/compliance competency, or other learnable job-specific capability. Examples include SQL, Excel, financial modelling, third-party risk management, due diligence, risk assessment, regulatory compliance, contract negotiation, recruitment, SEO and AutoCAD.

A soft skill is a transferable interpersonal or cognitive competency such as communication, collaboration, stakeholder management, leadership, problem solving, analytical thinking, presentation, negotiation, organization or adaptability.

Do not extract company names, team names, generic nouns, industries by themselves, benefits, degrees, years of experience, seniority, locations, personality fluff, or vague words such as 'business', 'management', 'support', 'reports', 'customers', 'projects', 'technology', 'risk' or 'finance' unless the text clearly names a professional competency (for example 'risk management' or 'financial analysis').

Prefer concise canonical names. Normalize common abbreviations and expanded forms to one canonical skill name across the whole response. For example, TPRM and third-party risk management should both become 'Third-Party Risk Management'; DCF and discounted cash flow should become one DCF skill; CRM and customer relationship management should become one CRM skill. If both an acronym and its expanded form appear, return only one canonical skill rather than duplicate entries.

Do not invent a skill merely because it would probably be useful for the role. Responsibility sections may provide evidence of skills, but only extract the competency actually demonstrated by the action. For example, 'assess third-party risks' can support 'Risk Assessment' and 'Third-Party Risk Management'; 'prepare reports' alone should not become a vague 'Reporting' skill unless the surrounding text makes a specific professional competency clear.

For eligibility, extract every concrete candidate prerequisite or logistical constraint that affects whether someone can apply or take the role. This includes years/type of experience, education level and field of study, current student status/year of study, graduation year or graduation window, internship duration/commitment, availability/start dates, full-time/part-time availability, work authorization/citizenship/visa constraints, required languages, certifications/licences/professional registration, security clearance, and physical requirements.

Do not infer missing details. Do not turn role location, ordinary employment type, responsibilities, benefits, employer descriptions, or application instructions into eligibility. For example, a role being labelled "Full-time" is not by itself a candidate availability requirement; "must be available full-time for 6 months" is. Preserve meaningful qualifiers such as minimum/maximum, preferred vs required, dates, durations, degree disciplines and alternative conditions.

For each skill and eligibility item, return a short exact evidence excerpt copied from the supplied section. Never use text from ignored company, benefits, application or legal sections because those sections are not supplied to you.
"""


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section_index": {
                        "type": "integer",
                    },
                    "canonical_name": {
                        "type": "string",
                    },
                    "skill_type": {
                        "type": "string",
                        "enum": [
                            "hard_skill",
                            "soft_skill",
                        ],
                    },
                    "evidence": {
                        "type": "string",
                    },
                    "confidence": {
                        "type": "number",
                    },
                },
                "required": [
                    "section_index",
                    "canonical_name",
                    "skill_type",
                    "evidence",
                    "confidence",
                ],
                "additionalProperties": False,
            },
        },
        "eligibility": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section_index": {"type": "integer"},
                    "requirement_type": {
                        "type": "string",
                        "enum": [
                            "experience", "education", "work_authorization",
                            "availability", "language", "certification",
                            "professional_registration", "licence",
                            "security_clearance", "physical_requirement"
                        ]
                    },
                    "evidence": {"type": "string"},
                    "requirement_level": {
                        "type": "string",
                        "enum": ["required", "preferred", "unknown"]
                    },
                    "confidence": {"type": "number"}
                },
                "required": [
                    "section_index", "requirement_type", "evidence",
                    "requirement_level", "confidence"
                ],
                "additionalProperties": False
            }
        }
    },
    "required": [
        "skills",
        "eligibility",
    ],
    "additionalProperties": False,
}


def model_skill_extraction_enabled():
    enabled = (
        os.getenv(
            "CAREERLENS_MODEL_SKILL_EXTRACTION",
            "",
        )
        .strip()
        .casefold()
        in TRUE_VALUES
    )

    return bool(
        enabled
        and os.getenv("OPENAI_API_KEY")
    )


def _model_name():
    return (
        os.getenv(
            "CAREERLENS_SKILL_MODEL",
            DEFAULT_MODEL,
        ).strip()
        or DEFAULT_MODEL
    )


def _select_sections(
    text,
    source_field,
):
    sections = split_job_sections(
        text,
        source_field=source_field,
    )

    candidates = [
        section
        for section in sections
        if (
            not section.is_ignored
            and section.section_type
            in ELIGIBLE_SECTION_TYPES
        )
    ]

    priority = {
        "requirements": 0,
        "preferred": 1,
        "responsibilities": 2,
        "role": 3,
        "other": 4,
    }

    candidates = sorted(
        enumerate(candidates),
        key=lambda item: (
            priority.get(
                item[1].section_type,
                9,
            ),
            item[0],
        ),
    )

    selected = []
    used_characters = 0

    for _, section in candidates:
        remaining = (
            MAX_SECTION_CHARACTERS
            - used_characters
        )

        if remaining <= 0:
            break

        section_text = (
            section.text[:remaining]
            .strip()
        )

        if not section_text:
            continue

        selected.append(
            JobSection(
                section_type=
                    section.section_type,
                heading=section.heading,
                text=section_text,
            )
        )

        used_characters += len(
            section_text
        )

    if selected:
        return selected

    # Section detection is a precision aid, not a hard gate. Provider pages
    # sometimes flatten or rename headings in ways our section classifier has
    # not seen yet. In that case, send the usable description as a neutral
    # section rather than silently skipping model extraction altogether.
    fallback_text = (
        text[:MAX_SECTION_CHARACTERS]
        .strip()
    )

    if fallback_text:
        message = (
            "[CareerLens skill model] section selector found 0 eligible "
            "sections; using full-description fallback."
        )
        logger.info(message)
        print(message, flush=True)

        return [
            JobSection(
                section_type="other",
                heading=(
                    "Job description fallback"
                ),
                text=fallback_text,
            )
        ]

    return []


def _build_user_payload(
    sections,
):
    return {
        "sections": [
            {
                "section_index": index,
                "section_type": (
                    section.section_type
                ),
                "heading": (
                    section.heading
                    or ""
                ),
                "text": section.text,
            }
            for index, section
            in enumerate(sections)
        ]
    }


def _extract_response_text(
    response_data,
):
    for output_item in (
        response_data.get("output")
        or []
    ):
        if output_item.get("type") != "message":
            continue

        for content in (
            output_item.get("content")
            or []
        ):
            if content.get("type") == "output_text":
                text_value = content.get(
                    "text"
                )

                if text_value:
                    return text_value

    return None


def _call_openai(
    sections,
):
    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:
        return []

    payload = {
        "model": _model_name(),
        "store": False,
        "instructions": SYSTEM_INSTRUCTIONS,
        "input": json.dumps(
            _build_user_payload(
                sections
            ),
            ensure_ascii=False,
        ),
        "text": {
            "format": {
                "type": "json_schema",
                "name": (
                    "careerlens_skill_extraction"
                ),
                "description": (
                    "Skills directly supported by "
                    "candidate-focused job sections."
                ),
                "schema": OUTPUT_SCHEMA,
                "strict": True,
            }
        },
    }

    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(
            payload
        ).encode("utf-8"),
        headers={
            "Authorization": (
                f"Bearer {api_key}"
            ),
            "Content-Type": (
                "application/json"
            ),
        },
        method="POST",
    )

    timeout = float(
        os.getenv(
            "CAREERLENS_SKILL_MODEL_TIMEOUT",
            "30",
        )
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            response_data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            "Skill model request failed "
            f"with HTTP {exc.code}: "
            f"{detail[:500]}"
        ) from exc

    text_value = _extract_response_text(
        response_data
    )

    if not text_value:
        raise RuntimeError(
            "Skill model returned no output text."
        )

    parsed = json.loads(
        text_value
    )

    return parsed


def _clean_model_skill(
    skill,
):
    name = str(
        skill.get(
            "canonical_name",
            "",
        )
    ).strip()

    skill_type = skill.get(
        "skill_type"
    )

    evidence = str(
        skill.get(
            "evidence",
            "",
        )
    ).strip()

    try:
        confidence = float(
            skill.get(
                "confidence",
                0,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        confidence = 0.0

    if not name:
        return None

    if skill_type not in {
        "hard_skill",
        "soft_skill",
    }:
        return None

    if confidence < 0.65:
        return None

    if not evidence:
        return None

    return {
        "canonical_name": name,
        "skill_type": skill_type,
        "evidence": evidence,
        "confidence": min(
            confidence,
            1.0,
        ),
    }


def _section_level(
    section,
):
    return infer_level_from_section(
        section.section_type,
        "unknown",
    )


def _find_existing_mention(
    mentions,
    evidence,
):
    normalized_evidence = (
        normalize_requirement_text(
            evidence
        )
    )

    for mention in mentions:
        if (
            mention.normalized_text
            == normalized_evidence
        ):
            return mention

    return None


def _append_model_skill(
    mention,
    skill,
):
    metadata = dict(
        mention.structured_value
        or {}
    )

    model_skills = list(
        metadata.get(
            "model_skills"
        )
        or []
    )

    existing_keys = {
        (
            str(item.get(
                "skill_type",
                "",
            )),
            str(item.get(
                "canonical_name",
                "",
            )).casefold(),
        )
        for item in model_skills
        if isinstance(
            item,
            dict,
        )
    }

    skill_key = (
        skill["skill_type"],
        skill[
            "canonical_name"
        ].casefold(),
    )

    if skill_key not in existing_keys:
        model_skills.append(
            skill
        )

    metadata[
        "model_skill_processed"
    ] = True

    metadata[
        "model_skill_provider"
    ] = "openai"

    metadata[
        "model_skill_model"
    ] = _model_name()

    metadata[
        "model_skills"
    ] = model_skills

    mention.structured_value = metadata


def enrich_manual_requirement_mentions(
    text,
    mentions,
    source_field="description",
):
    """Model-assist manual job extraction without making the model mandatory.

    If the feature flag/key is missing, or the model call fails, the original
    rule-based mentions are returned unchanged. This guarantees that model
    availability can never turn a valid job into a zero-result analysis.
    """

    if not text:
        message = (
            "[CareerLens skill model] enrichment invoked with empty text; "
            "using rule-based extraction."
        )
        logger.info(message)
        print(message, flush=True)
        return mentions

    entry_message = (
        "[CareerLens skill model] enrichment invoked "
        f"(characters={len(text)}, rule_mentions={len(mentions)})."
    )
    logger.info(entry_message)
    print(entry_message, flush=True)

    if not model_skill_extraction_enabled():
        message = (
            "[CareerLens skill model] disabled or OPENAI_API_KEY unavailable; "
            "using rule-based extraction."
        )
        logger.info(message)
        print(message, flush=True)
        return mentions

    sections = _select_sections(
        text,
        source_field,
    )

    if not sections:
        message = (
            "[CareerLens skill model] no usable section text after fallback; "
            "using rule-based extraction."
        )
        logger.info(message)
        print(message, flush=True)
        return mentions

    start_message = (
        "[CareerLens skill model] starting "
        f"{_model_name()} across {len(sections)} candidate-focused sections."
    )
    logger.info(start_message)
    print(start_message, flush=True)

    try:
        model_result = _call_openai(
            sections
        )
        model_skills = model_result.get("skills") or []
        model_eligibility = model_result.get("eligibility") or []

    except Exception as exc:
        failure_message = (
            "[CareerLens skill model] failed; using rule-based fallback: "
            f"{exc}"
        )
        logger.exception(failure_message)
        print(failure_message, flush=True)
        return mentions

    success_message = (
        "[CareerLens skill model] succeeded with "
        f"{len(model_skills)} raw skill candidates and "
        f"{len(model_eligibility)} eligibility candidates."
    )
    logger.info(success_message)
    print(success_message, flush=True)

    # The model has successfully reviewed the candidate-focused sections.
    # Mark existing skill-like mentions from those sections as processed even
    # when the model intentionally returns no skill for them. This prevents
    # the broad legacy phrase-capture rules from re-introducing text that the
    # verifier rejected (for example, years-of-experience wording).
    section_texts = [
        normalize_requirement_text(
            section.text
        )
        for section in sections
    ]

    for mention in mentions:
        if mention.requirement_type not in {
            "skill",
            "tool",
            "domain_knowledge",
            "experience",
            "other",
        }:
            continue

        normalized_mention = (
            mention.normalized_text
        )

        if not any(
            normalized_mention
            and normalized_mention
            in section_text
            for section_text in section_texts
        ):
            continue

        metadata = dict(
            mention.structured_value
            or {}
        )

        metadata[
            "model_skill_processed"
        ] = True

        metadata[
            "model_skill_provider"
        ] = "openai"

        metadata[
            "model_skill_model"
        ] = _model_name()

        metadata.setdefault(
            "model_skills",
            [],
        )

        mention.structured_value = metadata

    grouped = defaultdict(list)

    for raw_skill in model_skills:
        if not isinstance(
            raw_skill,
            dict,
        ):
            continue

        try:
            section_index = int(
                raw_skill.get(
                    "section_index"
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if not (
            0 <= section_index
            < len(sections)
        ):
            continue

        cleaned = _clean_model_skill(
            raw_skill
        )

        if cleaned is None:
            continue

        section = sections[
            section_index
        ]

        normalized_evidence = (
            normalize_requirement_text(
                cleaned["evidence"]
            )
        )

        normalized_section = (
            normalize_requirement_text(
                section.text
            )
        )

        # Evidence must be grounded in the section supplied to the model.
        # Reject invented/paraphrased evidence instead of creating a synthetic
        # requirement from unsupported text.
        if (
            not normalized_evidence
            or normalized_evidence
            not in normalized_section
        ):
            continue

        grouped[
            (
                section_index,
                cleaned["evidence"],
            )
        ].append(
            cleaned
        )

    for (
        section_index,
        evidence,
    ), skills in grouped.items():
        section = sections[
            section_index
        ]

        mention = _find_existing_mention(
            mentions,
            evidence,
        )

        if mention is None:
            metadata = (
                section.metadata()
            )

            metadata[
                "model_skill_processed"
            ] = True

            metadata[
                "model_skill_provider"
            ] = "openai"

            metadata[
                "model_skill_model"
            ] = _model_name()

            metadata[
                "model_skills"
            ] = []

            mention = RequirementMention(
                requirement_type="skill",
                raw_text=evidence,
                normalized_text=(
                    normalize_requirement_text(
                        evidence
                    )
                ),
                requirement_level=(
                    _section_level(
                        section
                    )
                ),
                rule_name=(
                    "model_skill_extractor"
                ),
                structured_value=metadata,
            )

            mentions.append(
                mention
            )

        for skill in skills:
            _append_model_skill(
                mention,
                skill,
            )

    # A successful model review is authoritative for eligibility-like
    # requirements in the reviewed candidate-focused sections. Remove broad
    # regex eligibility hits from those sections, then rebuild them from
    # model-verified exact evidence. This improves recall while preventing
    # keyword false positives (for example an incidental mention of a degree).
    eligibility_types = {
        "experience", "education", "work_authorization", "availability",
        "language", "certification", "professional_registration",
        "licence", "security_clearance", "physical_requirement",
    }

    reviewed_text = "\n".join(section.text for section in sections).casefold()
    mentions = [
        mention for mention in mentions
        if not (
            mention.requirement_type in eligibility_types
            and mention.raw_text.casefold() in reviewed_text
        )
    ]

    existing_eligibility = {
        (mention.requirement_type, mention.normalized_text)
        for mention in mentions
        if mention.requirement_type in eligibility_types
    }

    for item in model_eligibility:
        requirement_type = str(item.get("requirement_type", "")).strip()
        evidence = str(item.get("evidence", "")).strip()
        requirement_level = str(item.get("requirement_level", "unknown")).strip()
        try:
            confidence = float(item.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0.0

        section_index = item.get("section_index")
        if requirement_type not in eligibility_types or not evidence or confidence < 0.70:
            continue
        if not isinstance(section_index, int) or not (0 <= section_index < len(sections)):
            continue

        section = sections[section_index]
        # Exact-evidence validation is the anti-hallucination gate.
        if evidence.casefold() not in section.text.casefold():
            continue
        if requirement_level not in {"required", "preferred", "unknown"}:
            requirement_level = "unknown"
        if requirement_level == "unknown":
            requirement_level = _section_level(section)

        normalized = normalize_requirement_text(evidence)
        key = (requirement_type, normalized)
        if key in existing_eligibility:
            continue

        mentions.append(
            RequirementMention(
                requirement_type=requirement_type,
                raw_text=evidence,
                normalized_text=normalized,
                requirement_level=requirement_level,
                rule_name="model_verified_eligibility",
                structured_value={
                    **section.metadata(),
                    "model_eligibility_processed": True,
                    "model_eligibility_provider": "openai",
                    "model_eligibility_model": _model_name(),
                    "model_confidence": min(confidence, 1.0),
                },
            )
        )
        existing_eligibility.add(key)

    return mentions
