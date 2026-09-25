from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)
from src.services.job_fit_service import (
    assess_job_fit,
)
from src.user_profile.map_profile_concepts import (
    map_profile_concepts,
)


STATUS_STRENGTH = {
    "gap": 0,
    "candidate": 1,
    "claimed_only": 2,
    "evidenced": 3,
}


def _latest_resume_text(
    connection,
    profile_id,
):
    return (
        connection.execute(
            text(
                """
                SELECT
                    raw_text

                FROM
                    resume_documents

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


def _collect_review_concepts(
    analysis,
):
    profile_fit = analysis.get(
        "profile_fit"
    )

    if (
        not isinstance(
            profile_fit,
            dict,
        )
        or profile_fit.get(
            "status"
        )
        != "assessed"
    ):
        return []

    concepts = {}
    level_strength = {
        "unknown": 1,
        "preferred": 2,
        "required": 3,
    }

    for group in (
        profile_fit.get(
            "groups"
        )
        or []
    ):
        requirement_level = (
            group.get(
                "level"
            )
            or "unknown"
        )

        for concept in (
            group.get(
                "concepts"
            )
            or []
        ):
            if (
                concept.get(
                    "type"
                )
                not in {
                    "hard_skill",
                    "soft_skill",
                }
            ):
                continue

            if (
                concept.get(
                    "fit_status"
                )
                == "evidenced"
            ):
                continue

            concept_id = concept.get(
                "concept_id"
            )

            if concept_id is None:
                continue

            existing = concepts.get(
                concept_id
            )

            candidate = {
                "concept_id":
                    concept_id,

                "name":
                    concept.get(
                        "name"
                    )
                    or "",

                "type":
                    concept.get(
                        "type"
                    ),

                "fit_status":
                    concept.get(
                        "fit_status"
                    )
                    or "gap",

                "requirement_level":
                    requirement_level,
            }

            if (
                existing is None
                or level_strength.get(
                    requirement_level,
                    0,
                )
                >
                level_strength.get(
                    existing[
                        "requirement_level"
                    ],
                    0,
                )
            ):
                concepts[
                    concept_id
                ] = candidate

    return list(
        concepts.values()
    )


def _upgraded_status(
    baseline,
    model_result,
):
    if not model_result:
        return baseline

    status = model_result.get(
        "status"
    )

    confidence = float(
        model_result.get(
            "confidence",
            0,
        )
        or 0
    )

    if (
        status == "evidenced"
        and confidence >= 0.70
    ):
        candidate = "evidenced"

    elif (
        status == "claimed_only"
        and confidence >= 0.72
    ):
        candidate = "claimed_only"

    elif (
        status == "candidate"
        and confidence >= 0.65
    ):
        candidate = "candidate"

    else:
        return baseline

    if (
        STATUS_STRENGTH.get(
            candidate,
            -1,
        )
        >
        STATUS_STRENGTH.get(
            baseline,
            -1,
        )
    ):
        return candidate

    return baseline


def _reassess_group(
    group,
):
    concepts = (
        group.get(
            "concepts"
        )
        or []
    )

    if not concepts:
        group[
            "status"
        ] = "needs_review"
        return

    operator = (
        group.get(
            "operator"
        )
        or "all_of"
    )

    if operator == "any_of":
        strongest = max(
            concepts,
            key=lambda concept:
                STATUS_STRENGTH.get(
                    concept.get(
                        "fit_status"
                    ),
                    -1,
                ),
        )

        strongest_status = (
            strongest.get(
                "fit_status"
            )
            or "gap"
        )

        if (
            strongest_status
            == "gap"
            and group.get(
                "is_open"
            )
        ):
            group[
                "status"
            ] = "needs_review"

        else:
            group[
                "status"
            ] = strongest_status

        return

    weakest = min(
        concepts,
        key=lambda concept:
            STATUS_STRENGTH.get(
                concept.get(
                    "fit_status"
                ),
                -1,
            ),
    )

    group[
        "status"
    ] = (
        weakest.get(
            "fit_status"
        )
        or "gap"
    )


def _refresh_summary(
    profile_fit,
):
    groups = (
        profile_fit.get(
            "groups"
        )
        or []
    )

    unresolved = (
        profile_fit.get(
            "unresolved_requirements"
        )
        or []
    )

    summary = profile_fit.get(
        "summary"
    )

    if not isinstance(
        summary,
        dict,
    ):
        return

    statuses = [
        group.get(
            "status"
        )
        for group in groups
    ]

    summary[
        "evidenced_requirement_groups"
    ] = statuses.count(
        "evidenced"
    )

    summary[
        "claimed_only_requirement_groups"
    ] = statuses.count(
        "claimed_only"
    )

    summary[
        "candidate_requirement_groups"
    ] = statuses.count(
        "candidate"
    )

    summary[
        "gap_requirement_groups"
    ] = statuses.count(
        "gap"
    )

    summary[
        "required_candidate_groups"
    ] = sum(
        1
        for group in groups
        if (
            group.get(
                "level"
            )
            == "required"
            and group.get(
                "status"
            )
            == "candidate"
        )
    )

    summary[
        "required_gap_groups"
    ] = sum(
        1
        for group in groups
        if (
            group.get(
                "level"
            )
            == "required"
            and group.get(
                "status"
            )
            == "gap"
        )
    )

    summary[
        "unresolved_requirements"
    ] = (
        len(
            unresolved
        )
        + statuses.count(
            "needs_review"
        )
    )


def _apply_model_results(
    analysis,
    model_results,
):
    if not model_results:
        return analysis

    profile_fit = analysis.get(
        "profile_fit"
    )

    if (
        not isinstance(
            profile_fit,
            dict,
        )
        or profile_fit.get(
            "status"
        )
        != "assessed"
    ):
        return analysis

    for group in (
        profile_fit.get(
            "groups"
        )
        or []
    ):
        for concept in (
            group.get(
                "concepts"
            )
            or []
        ):
            concept_id = concept.get(
                "concept_id"
            )

            model_result = (
                model_results.get(
                    concept_id
                )
            )

            if not model_result:
                continue

            baseline = (
                concept.get(
                    "fit_status"
                )
                or "gap"
            )

            model_evidence = (
                model_result.get(
                    "evidence"
                )
            )

            model_confidence = (
                model_result.get(
                    "confidence"
                )
            )

            model_status = (
                model_result.get(
                    "status"
                )
            )

            if (
                model_status
                != "unsupported"
                and model_evidence
            ):
                concept[
                    "model_evidence"
                ] = model_evidence

                concept[
                    "model_confidence"
                ] = model_confidence

                concept[
                    "model_match_status"
                ] = model_status

            upgraded = (
                _upgraded_status(
                    baseline,
                    model_result,
                )
            )

            if upgraded == baseline:
                continue

            concept[
                "fit_status"
            ] = upgraded

            if upgraded == "evidenced":
                concept[
                    "claim_status"
                ] = "confirmed"

                concept[
                    "evidence_status"
                ] = "confirmed"

            elif upgraded == "claimed_only":
                concept[
                    "claim_status"
                ] = "confirmed"

            elif upgraded == "candidate":
                concept[
                    "evidence_status"
                ] = "candidate"


        _reassess_group(
            group
        )

    _refresh_summary(
        profile_fit
    )

    profile_fit[
        "resume_matching_method"
    ] = "baseline_plus_model_verification"

    return analysis


def assess_manual_job_fit(
    profile_id,
    job_id,
    database_url=None,
):
    engine = create_database_engine(
        database_url
    )

    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        (
                            SELECT
                                1

                            FROM
                                manual_job_imports

                            WHERE
                                profile_id =
                                    :profile_id

                                AND
                                job_id =
                                    :job_id

                            LIMIT 1
                        )
                        AS owned,

                        (
                            SELECT
                                raw_text

                            FROM
                                resume_documents

                            WHERE
                                profile_id =
                                    :profile_id

                            ORDER BY
                                resume_id DESC

                            LIMIT 1
                        )
                        AS resume_text;
                    """
                ),
                {
                    "profile_id":
                        profile_id,

                    "job_id":
                        job_id,
                },
            )
            .mappings()
            .one()
        )

    if row[
        "owned"
    ] is None:
        raise ValueError(
            "Imported job not found."
        )

    # New manual jobs can introduce concepts that did not exist when the
    # resume was originally mapped.
    map_profile_concepts(
        profile_id=
            profile_id,

        database_url=
            database_url,
    )

    # Always build the existing deterministic comparison first.
    analysis = assess_job_fit(
        profile_id=
            profile_id,

        job_id=
            job_id,

        database_url=
            database_url,
    )

    review_concepts = (
        _collect_review_concepts(
            analysis
        )
    )

    if (
        not row[
            "resume_text"
        ]
        or not review_concepts
    ):
        return analysis

    # IMPORTANT: lazy import. The OpenAI helper is not imported while FastAPI
    # starts, so model code cannot block Render port binding or app startup.
    try:
        from src.user_profile.model_resume_matcher import (
            verify_resume_skills,
        )

        model_results = (
            verify_resume_skills(
                row[
                    "resume_text"
                ],
                review_concepts,
            )
        )

    except Exception:
        # Baseline CareerLens comparison is always the fallback.
        return analysis

    return _apply_model_results(
        analysis,
        model_results,
    )
