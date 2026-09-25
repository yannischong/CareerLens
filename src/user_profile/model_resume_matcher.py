import json
import logging
import os
import re
import urllib.error
import urllib.request

from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)


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

logger = logging.getLogger(__name__)


SYSTEM_INSTRUCTIONS = """You verify whether a candidate's resume supports specific job-skill concepts.

You receive:
1. A resume.
2. A list of already-extracted job concepts, each with a concept_id, canonical skill name, hard/soft skill type, requirement level, and the current CareerLens baseline fit status.

For every supplied concept, classify the resume support as exactly one of:
- evidenced: the resume contains concrete evidence demonstrating the skill.
- claimed_only: the resume explicitly lists or claims the skill, but does not clearly demonstrate use.
- candidate: the resume contains related evidence, but it is not strong enough to confirm the exact skill.
- unsupported: the resume does not support the skill.

Rules:
- Be conservative. Do not infer a hard skill merely from a job title, employer, degree, industry, or adjacent skill.
- Hard skills should be explicitly named or demonstrated by an unmistakably equivalent activity.
- A software/tool requirement should normally require that tool or a clearly equivalent named tool to appear in the resume.
- Domain competencies such as third-party risk management, financial modelling, due diligence, risk assessment, regulatory compliance, recruitment, SEO, contract negotiation, etc. may be evidenced by concrete resume bullets that clearly describe performing that competency.
- Soft skills can be evidenced through concrete actions. For example, presenting to senior stakeholders can evidence Presentation / Communication; coordinating multiple teams can evidence Collaboration / Stakeholder Management.
- Do not treat generic personality claims as strong evidence.
- Do not invent experience.
- The evidence field must be a short exact excerpt copied from the resume. If unsupported, return an empty evidence string.
- Preserve the supplied concept_id exactly.
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
                "additionalProperties": False,
            },
        }
    },
    "required": [
        "matches",
    ],
    "additionalProperties": False,
}


def _truthy_environment(
    name,
):
    value = os.getenv(
        name,
        "",
    )

    return (
        value.strip().casefold()
        in TRUE_VALUES
    )


def model_resume_matching_enabled():
    # A separate flag can override the general model-extraction switch.
    # If it is absent, reuse the existing CareerLens AI extraction flag so
    # current deployments do not need another environment variable.
    explicit = os.getenv(
        "CAREERLENS_MODEL_RESUME_MATCHING"
    )

    if explicit is not None:
        enabled = (
            explicit.strip().casefold()
            in TRUE_VALUES
        )
    else:
        enabled = _truthy_environment(
            "CAREERLENS_MODEL_SKILL_EXTRACTION"
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
        response_data.get("output")
        or []
    ):
        if (
            output_item.get("type")
            != "message"
        ):
            continue

        for content in (
            output_item.get("content")
            or []
        ):
            if (
                content.get("type")
                != "output_text"
            ):
                continue

            value = content.get(
                "text"
            )

            if value:
                return value

    return None


def _normalize_for_grounding(
    value,
):
    return re.sub(
        r"\s+",
        " ",
        str(
            value
            or ""
        ),
    ).strip().casefold()


def _fetch_resume_text(
    connection,
    profile_id,
):
    return (
        connection.execute(
            text(
                """
                SELECT
                    raw_text

                FROM resume_documents

                WHERE
                    profile_id =
                        :profile_id

                ORDER BY
                    resume_id DESC

                LIMIT 1;
                """
            ),
            {
                "profile_id":
                    profile_id,
            },
        )
        .scalar_one_or_none()
    )


def _build_payload(
    resume_text,
    concepts,
):
    return {
        "resume": (
            resume_text[
                :MAX_RESUME_CHARACTERS
            ]
        ),
        "job_concepts": [
            {
                "concept_id":
                    int(
                        item[
                            "concept_id"
                        ]
                    ),
                "canonical_name":
                    item[
                        "canonical_name"
                    ],
                "concept_type":
                    item[
                        "concept_type"
                    ],
                "requirement_level":
                    item.get(
                        "requirement_level"
                    )
                    or "unknown",
                "baseline_fit_status":
                    item.get(
                        "fit_status"
                    )
                    or "gap",
            }
            for item in concepts
        ],
    }


def _call_openai(
    resume_text,
    concepts,
):
    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:
        return []

    payload = {
        "model":
            _model_name(),

        "store":
            False,

        "instructions":
            SYSTEM_INSTRUCTIONS,

        "input":
            json.dumps(
                _build_payload(
                    resume_text,
                    concepts,
                ),
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
                        "Grounded resume support "
                        "for job-skill concepts."
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
            os.getenv(
                "CAREERLENS_SKILL_MODEL_TIMEOUT",
                "30",
            ),
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
            exc.read()
            .decode(
                "utf-8",
                errors="replace",
            )
        )

        raise RuntimeError(
            "Resume-match model request "
            f"failed with HTTP {exc.code}: "
            f"{detail[:500]}"
        ) from exc

    text_value = _extract_response_text(
        response_data
    )

    if not text_value:
        raise RuntimeError(
            "Resume-match model returned "
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
        _normalize_for_grounding(
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

        if status not in {
            "evidenced",
            "claimed_only",
            "candidate",
            "unsupported",
        }:
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

        if (
            status
            != "unsupported"
        ):
            normalized_evidence = (
                _normalize_for_grounding(
                    evidence
                )
            )

            # Never accept an invented or paraphrased quotation as proof.
            if (
                not normalized_evidence
                or normalized_evidence
                not in normalized_resume
            ):
                continue

        cleaned[
            concept_id
        ] = {
            "concept_id":
                concept_id,

            "status":
                status,

            "evidence":
                evidence,

            "confidence":
                confidence,
        }

    return cleaned


def verify_resume_concepts(
    profile_id,
    concepts,
    database_url=None,
):
    """Return grounded model judgements for weak/uncertain concept matches.

    The function is additive: callers should use it only to upgrade uncertain
    baseline matches. If the model is disabled or fails, an empty mapping is
    returned and the existing CareerLens comparison remains unchanged.
    """

    if not concepts:
        return {}

    if not model_resume_matching_enabled():
        return {}

    review_concepts = [
        concept
        for concept in concepts
        if (
            concept.get(
                "fit_status"
            )
            != "evidenced"
        )
    ]

    if not review_concepts:
        return {}

    engine = create_database_engine(
        database_url
    )

    with engine.connect() as connection:
        resume_text = (
            _fetch_resume_text(
                connection,
                profile_id,
            )
        )

    if not resume_text:
        return {}

    try:
        raw_results = _call_openai(
            resume_text,
            review_concepts,
        )

    except Exception:
        logger.exception(
            "[CareerLens resume model] "
            "verification failed; retaining "
            "baseline resume comparison."
        )
        return {}

    return _clean_results(
        raw_results,
        review_concepts,
        resume_text,
    )
