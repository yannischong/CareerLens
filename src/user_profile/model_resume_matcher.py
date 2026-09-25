import json
import logging
import os
import re
import urllib.error
import urllib.request


OPENAI_RESPONSES_URL = (
    "https://api.openai.com/v1/responses"
)

DEFAULT_MODEL = "gpt-5.6-luna"

MAX_RESUME_CHARACTERS = 28000

TRUE_VALUES = {
    "1",
    "true",
    "yes",
    "on",
}

VALID_STATUSES = {
    "evidenced",
    "claimed_only",
    "candidate",
    "unsupported",
}

logger = logging.getLogger(__name__)


SYSTEM_INSTRUCTIONS = """You verify whether a candidate's resume supports specific job-skill concepts.

You receive:
1. Resume text.
2. A list of already-extracted job skills.

For every supplied skill, classify resume support as exactly one of:
- evidenced: concrete resume evidence demonstrates the skill.
- claimed_only: the resume explicitly names/claims the skill, but does not clearly demonstrate use.
- candidate: related evidence exists, but it is not strong enough to confirm the exact skill.
- unsupported: the resume does not support the skill.

Rules:
- Be conservative.
- Do not infer a hard skill merely from a job title, company, degree, industry, or adjacent skill.
- Software/tools normally require that tool, or an unmistakably equivalent named tool, to appear.
- Domain skills may be evidenced by concrete bullets clearly describing performance of that competency.
- Soft skills can be evidenced by actions. For example, presenting to senior stakeholders can evidence presentation/communication; coordinating multiple teams can evidence collaboration/stakeholder management.
- Do not invent experience.
- Evidence must be a short exact excerpt copied from the supplied resume.
- If unsupported, evidence must be an empty string.
- Preserve concept_id exactly.
"""


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "matches": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "concept_id": {
                        "type": "integer",
                    },
                    "status": {
                        "type": "string",
                        "enum": [
                            "evidenced",
                            "claimed_only",
                            "candidate",
                            "unsupported",
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
                    "concept_id",
                    "status",
                    "evidence",
                    "confidence",
                ],
                "additionalProperties":
                    False,
            },
        }
    },
    "required": [
        "matches",
    ],
    "additionalProperties":
        False,
}


def model_resume_matching_enabled():
    explicit = os.getenv(
        "CAREERLENS_MODEL_RESUME_MATCHING"
    )

    if explicit is not None:
        enabled = (
            explicit.strip().casefold()
            in TRUE_VALUES
        )
    else:
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
        and os.getenv(
            "OPENAI_API_KEY"
        )
    )


def _model_name():
    return (
        os.getenv(
            "CAREERLENS_RESUME_MATCH_MODEL",
            os.getenv(
                "CAREERLENS_SKILL_MODEL",
                DEFAULT_MODEL,
            ),
        ).strip()
        or DEFAULT_MODEL
    )


def _extract_response_text(
    response_data,
):
    for output_item in (
        response_data.get(
            "output"
        )
        or []
    ):
        if (
            output_item.get(
                "type"
            )
            != "message"
        ):
            continue

        for content in (
            output_item.get(
                "content"
            )
            or []
        ):
            if (
                content.get(
                    "type"
                )
                != "output_text"
            ):
                continue

            value = content.get(
                "text"
            )

            if value:
                return value

    return None


def _normalize_text(
    value,
):
    return (
        re.sub(
            r"\s+",
            " ",
            str(
                value
                or ""
            ),
        )
        .strip()
        .casefold()
    )


def _call_openai(
    resume_text,
    concepts,
):
    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:
        return []

    input_payload = {
        "resume":
            resume_text[
                :MAX_RESUME_CHARACTERS
            ],

        "job_skills": [
            {
                "concept_id":
                    int(
                        concept[
                            "concept_id"
                        ]
                    ),

                "name":
                    concept[
                        "name"
                    ],

                "type":
                    concept[
                        "type"
                    ],

                "requirement_level":
                    concept.get(
                        "requirement_level",
                        "unknown",
                    ),

                "baseline_fit_status":
                    concept.get(
                        "fit_status",
                        "gap",
                    ),
            }
            for concept in concepts
        ],
    }

    payload = {
        "model":
            _model_name(),

        "store":
            False,

        "instructions":
            SYSTEM_INSTRUCTIONS,

        "input":
            json.dumps(
                input_payload,
                ensure_ascii=False,
            ),

        "text": {
            "format": {
                "type":
                    "json_schema",

                "name":
                    "careerlens_resume_skill_match",

                "description":
                    (
                        "Grounded support for "
                        "job skills in a resume."
                    ),

                "schema":
                    OUTPUT_SCHEMA,

                "strict":
                    True,
            }
        },
    }

    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(
            payload
        ).encode(
            "utf-8"
        ),
        headers={
            "Authorization":
                f"Bearer {api_key}",

            "Content-Type":
                "application/json",
        },
        method="POST",
    )

    timeout = float(
        os.getenv(
            "CAREERLENS_RESUME_MATCH_TIMEOUT",
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
        detail = (
            exc.read().decode(
                "utf-8",
                errors="replace",
            )
        )

        raise RuntimeError(
            "Resume model HTTP "
            f"{exc.code}: "
            f"{detail[:500]}"
        ) from exc

    text_value = _extract_response_text(
        response_data
    )

    if not text_value:
        raise RuntimeError(
            "Resume model returned "
            "no output text."
        )

    parsed = json.loads(
        text_value
    )

    return (
        parsed.get(
            "matches"
        )
        or []
    )


def _clean_results(
    raw_results,
    concepts,
    resume_text,
):
    valid_ids = {
        int(
            concept[
                "concept_id"
            ]
        )
        for concept in concepts
    }

    normalized_resume = (
        _normalize_text(
            resume_text
        )
    )

    cleaned = {}

    for raw in raw_results:
        if not isinstance(
            raw,
            dict,
        ):
            continue

        try:
            concept_id = int(
                raw.get(
                    "concept_id"
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if concept_id not in valid_ids:
            continue

        status = raw.get(
            "status"
        )

        if status not in VALID_STATUSES:
            continue

        try:
            confidence = float(
                raw.get(
                    "confidence",
                    0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            confidence = 0.0

        confidence = max(
            0.0,
            min(
                confidence,
                1.0,
            ),
        )

        evidence = str(
            raw.get(
                "evidence",
                "",
            )
            or ""
        ).strip()

        if status != "unsupported":
            normalized_evidence = (
                _normalize_text(
                    evidence
                )
            )

            # Only accept evidence that is actually present in the resume.
            if (
                not normalized_evidence
                or normalized_evidence
                not in normalized_resume
            ):
                continue

        cleaned[
            concept_id
        ] = {
            "status":
                status,

            "evidence":
                evidence,

            "confidence":
                confidence,
        }

    return cleaned


def verify_resume_skills(
    resume_text,
    concepts,
):
    """Return model judgements without any DB access.

    This module is intentionally DB-free and is imported lazily by the
    manual-fit service so it cannot affect FastAPI startup.
    """

    if (
        not resume_text
        or not concepts
        or not model_resume_matching_enabled()
    ):
        return {}

    try:
        raw_results = (
            _call_openai(
                resume_text,
                concepts,
            )
        )

    except Exception:
        logger.exception(
            "[CareerLens resume model] "
            "verification failed; using "
            "baseline comparison."
        )
        return {}

    return _clean_results(
        raw_results,
        concepts,
        resume_text,
    )
