from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)
from src.matching.assess_fit import (
    CONCEPT_VERSION,
    FIT_VERSION,
    MAPPER_VERSION,
    REQUIREMENT_VERSION,
    assess_group,
    get_direct_fit_status,
)


def _job_row(
    connection,
    job_id,
):
    return (
        connection.execute(
            text(
                """
                SELECT
                    j.job_id,
                    j.raw_title,
                    j.raw_company_name,
                    j.location_raw,
                    j.employment_type,
                    j.job_url,
                    j.source,
                    j.description,

                    EXISTS (
                        SELECT 1

                        FROM job_quality_flags q

                        WHERE
                            q.job_id =
                                j.job_id

                            AND
                            q.generated_by =
                                'normalize_v1'

                            AND
                            q.flag_code =
                                'insufficient_description'
                    )
                    AS insufficient_description

                FROM jobs j

                WHERE
                    j.job_id =
                        :job_id;
                """
            ),
            {
                "job_id":
                    job_id,
            },
        )
        .mappings()
        .one_or_none()
    )


def _profile_has_resume(
    connection,
    profile_id,
):
    return connection.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1

                FROM resume_documents

                WHERE
                    profile_id =
                        :profile_id
            );
            """
        ),
        {
            "profile_id":
                profile_id,
        },
    ).scalar_one()


def _profile_status(
    connection,
    profile_id,
):
    rows = (
        connection.execute(
            text(
                """
                SELECT
                    concept_id,
                    claim_status,
                    evidence_status

                FROM
                    profile_concept_status

                WHERE
                    profile_id =
                        :profile_id

                    AND
                    mapper_version =
                        :mapper_version;
                """
            ),
            {
                "profile_id":
                    profile_id,

                "mapper_version":
                    MAPPER_VERSION,
            },
        )
        .mappings()
        .all()
    )


    return {
        row[
            "concept_id"
        ]: {
            "claim_status":
                row[
                    "claim_status"
                ],

            "evidence_status":
                row[
                    "evidence_status"
                ],
        }

        for row in rows
    }


def _job_requirement_rows(
    connection,
    job_id,
):
    rows = (
        connection.execute(
            text(
                """
                SELECT
                    r.requirement_mention_id,
                    r.requirement_type,
                    r.requirement_level,
                    r.raw_text,

                    jrc.concept_id,
                    jrc.group_operator,
                    jrc.group_is_open,

                    c.concept_type,
                    c.canonical_name

                FROM
                    job_requirement_mentions r

                JOIN
                    job_requirement_concepts jrc

                    ON
                        jrc.requirement_mention_id =
                        r.requirement_mention_id

                JOIN
                    requirement_concepts c

                    ON
                        c.concept_id =
                        jrc.concept_id

                WHERE
                    r.job_id =
                        :job_id

                    AND
                    r.extractor_version =
                        :requirement_version

                    AND
                    jrc.extractor_version =
                        :concept_version

                ORDER BY
                    r.requirement_mention_id,
                    c.concept_id;
                """
            ),
            {
                "job_id":
                    job_id,

                "requirement_version":
                    REQUIREMENT_VERSION,

                "concept_version":
                    CONCEPT_VERSION,
            },
        )
        .mappings()
        .all()
    )


    unresolved = (
        connection.execute(
            text(
                """
                SELECT
                    r.requirement_mention_id,
                    r.requirement_type,
                    r.requirement_level,
                    r.raw_text

                FROM
                    job_requirement_mentions r

                WHERE
                    r.job_id =
                        :job_id

                    AND
                    r.extractor_version =
                        :requirement_version

                    AND NOT EXISTS (
                        SELECT 1

                        FROM
                            job_requirement_concepts jrc

                        WHERE
                            jrc.requirement_mention_id =
                                r.requirement_mention_id

                            AND
                            jrc.extractor_version =
                                :concept_version
                    )

                ORDER BY
                    r.requirement_mention_id;
                """
            ),
            {
                "job_id":
                    job_id,

                "requirement_version":
                    REQUIREMENT_VERSION,

                "concept_version":
                    CONCEPT_VERSION,
            },
        )
        .mappings()
        .all()
    )


    return (
        rows,
        unresolved,
    )


def _build_results(
    rows,
    profile_status,
):
    groups = {}
    concept_results_by_id = {}


    level_strength = {
        "unknown": 1,
        "preferred": 2,
        "required": 3,
    }


    for row in rows:

        mention_id = row[
            "requirement_mention_id"
        ]


        if mention_id not in groups:

            groups[
                mention_id
            ] = {
                "requirement_mention_id":
                    mention_id,

                "requirement_type":
                    row[
                        "requirement_type"
                    ],

                "requirement_level":
                    row[
                        "requirement_level"
                    ],

                "raw_text":
                    row[
                        "raw_text"
                    ],

                "group_operator":
                    row[
                        "group_operator"
                    ],

                "group_is_open":
                    row[
                        "group_is_open"
                    ],

                "members":
                    [],
            }


        direct = (
            get_direct_fit_status(
                row[
                    "concept_id"
                ],

                profile_status,
            )
        )


        member = {
            "concept_id":
                row[
                    "concept_id"
                ],

            "concept_type":
                row[
                    "concept_type"
                ],

            "canonical_name":
                row[
                    "canonical_name"
                ],

            "claim_status":
                direct[
                    "claim_status"
                ],

            "evidence_status":
                direct[
                    "evidence_status"
                ],

            "fit_status":
                direct[
                    "fit_status"
                ],
        }


        groups[
            mention_id
        ][
            "members"
        ].append(
            member
        )


        concept_id = member[
            "concept_id"
        ]


        existing = (
            concept_results_by_id
            .get(
                concept_id
            )
        )


        current_level = (
            row[
                "requirement_level"
            ]
        )


        if (
            existing is None

            or
            level_strength.get(
                current_level,
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

            concept_results_by_id[
                concept_id
            ] = {
                **member,

                "requirement_level":
                    current_level,
            }


    group_results = []


    for group in groups.values():

        assessment = (
            assess_group(
                group
            )
        )


        group_results.append(
            {
                **group,
                **assessment,
            }
        )


    return (
        list(
            concept_results_by_id
            .values()
        ),

        group_results,
    )


def _persist_fit(
    connection,
    profile_id,
    job_id,
    concept_results,
    group_results,
    unresolved,
):
    connection.execute(
        text(
            """
            DELETE FROM
                job_profile_concept_fit

            WHERE
                profile_id =
                    :profile_id

                AND
                job_id =
                    :job_id

                AND
                fit_version =
                    :fit_version;
            """
        ),
        {
            "profile_id":
                profile_id,

            "job_id":
                job_id,

            "fit_version":
                FIT_VERSION,
        },
    )


    for result in concept_results:

        connection.execute(
            text(
                """
                INSERT INTO
                    job_profile_concept_fit (
                        profile_id,
                        job_id,
                        concept_id,
                        requirement_type,
                        requirement_level,
                        claim_status,
                        evidence_status,
                        fit_status,
                        fit_version
                    )

                VALUES (
                    :profile_id,
                    :job_id,
                    :concept_id,
                    :requirement_type,
                    :requirement_level,
                    :claim_status,
                    :evidence_status,
                    :fit_status,
                    :fit_version
                );
                """
            ),
            {
                "profile_id":
                    profile_id,

                "job_id":
                    job_id,

                "concept_id":
                    result[
                        "concept_id"
                    ],

                "requirement_type":
                    result[
                        "concept_type"
                    ],

                "requirement_level":
                    result[
                        "requirement_level"
                    ],

                "claim_status":
                    result[
                        "claim_status"
                    ],

                "evidence_status":
                    result[
                        "evidence_status"
                    ],

                "fit_status":
                    result[
                        "fit_status"
                    ],

                "fit_version":
                    FIT_VERSION,
            },
        )


    connection.execute(
        text(
            """
            DELETE FROM
                job_profile_requirement_group_fit

            WHERE
                profile_id =
                    :profile_id

                AND
                fit_version =
                    :fit_version

                AND
                requirement_mention_id
                IN (
                    SELECT
                        requirement_mention_id

                    FROM
                        job_requirement_mentions

                    WHERE
                        job_id =
                            :job_id
                );
            """
        ),
        {
            "profile_id":
                profile_id,

            "job_id":
                job_id,

            "fit_version":
                FIT_VERSION,
        },
    )


    for group in group_results:

        connection.execute(
            text(
                """
                INSERT INTO
                    job_profile_requirement_group_fit (
                        profile_id,
                        requirement_mention_id,
                        group_operator,
                        group_is_open,
                        assessment_status,
                        matched_concept_id,
                        assessment_method,
                        explanation,
                        fit_version
                    )

                VALUES (
                    :profile_id,
                    :requirement_mention_id,
                    :group_operator,
                    :group_is_open,
                    :assessment_status,
                    :matched_concept_id,
                    'logical_concept_group',
                    :explanation,
                    :fit_version
                );
                """
            ),
            {
                "profile_id":
                    profile_id,

                "requirement_mention_id":
                    group[
                        "requirement_mention_id"
                    ],

                "group_operator":
                    group[
                        "group_operator"
                    ],

                "group_is_open":
                    group[
                        "group_is_open"
                    ],

                "assessment_status":
                    group[
                        "assessment_status"
                    ],

                "matched_concept_id":
                    group[
                        "matched_concept_id"
                    ],

                "explanation":
                    group[
                        "explanation"
                    ],

                "fit_version":
                    FIT_VERSION,
            },
        )


    connection.execute(
        text(
            """
            DELETE FROM
                job_profile_requirement_checks

            WHERE
                profile_id =
                    :profile_id

                AND
                fit_version =
                    :fit_version

                AND
                requirement_mention_id
                IN (
                    SELECT
                        requirement_mention_id

                    FROM
                        job_requirement_mentions

                    WHERE
                        job_id =
                            :job_id
                );
            """
        ),
        {
            "profile_id":
                profile_id,

            "job_id":
                job_id,

            "fit_version":
                FIT_VERSION,
        },
    )


    for requirement in unresolved:

        connection.execute(
            text(
                """
                INSERT INTO
                    job_profile_requirement_checks (
                        profile_id,
                        requirement_mention_id,
                        assessment_status,
                        assessment_method,
                        explanation,
                        fit_version
                    )

                VALUES (
                    :profile_id,
                    :requirement_mention_id,
                    'needs_review',
                    'unmapped_requirement',
                    :explanation,
                    :fit_version
                );
                """
            ),
            {
                "profile_id":
                    profile_id,

                "requirement_mention_id":
                    requirement[
                        "requirement_mention_id"
                    ],

                "explanation":
                    (
                        "This requirement has "
                        "not yet been mapped to "
                        "an assessable profile "
                        "concept."
                    ),

                "fit_version":
                    FIT_VERSION,
            },
        )


def _summary_values(
    concept_results,
    group_results,
    unresolved,
):
    total_concepts = len(
        concept_results
    )


    required_concepts = sum(
        1
        for result in concept_results
        if (
            result[
                "requirement_level"
            ]
            == "required"
        )
    )


    preferred_concepts = sum(
        1
        for result in concept_results
        if (
            result[
                "requirement_level"
            ]
            == "preferred"
        )
    )


    unknown_level_concepts = (
        total_concepts
        - required_concepts
        - preferred_concepts
    )


    evidenced_concepts = sum(
        1
        for result in concept_results
        if (
            result[
                "fit_status"
            ]
            == "evidenced"
        )
    )


    claimed_only_concepts = sum(
        1
        for result in concept_results
        if (
            result[
                "fit_status"
            ]
            == "claimed_only"
        )
    )


    candidate_concepts = sum(
        1
        for result in concept_results
        if (
            result[
                "fit_status"
            ]
            == "candidate"
        )
    )


    gap_concepts = sum(
        1
        for result in concept_results
        if (
            result[
                "fit_status"
            ]
            == "gap"
        )
    )


    required_candidate_concepts = sum(
        1
        for result in concept_results
        if (
            result[
                "requirement_level"
            ]
            == "required"

            and
            result[
                "fit_status"
            ]
            == "candidate"
        )
    )


    required_gap_concepts = sum(
        1
        for result in concept_results
        if (
            result[
                "requirement_level"
            ]
            == "required"

            and
            result[
                "fit_status"
            ]
            == "gap"
        )
    )


    total_groups = len(
        group_results
    )


    required_groups = sum(
        1
        for group in group_results
        if (
            group[
                "requirement_level"
            ]
            == "required"
        )
    )


    preferred_groups = sum(
        1
        for group in group_results
        if (
            group[
                "requirement_level"
            ]
            == "preferred"
        )
    )


    unknown_groups = (
        total_groups
        - required_groups
        - preferred_groups
    )


    evidenced_groups = sum(
        1
        for group in group_results
        if (
            group[
                "assessment_status"
            ]
            == "evidenced"
        )
    )


    claimed_only_groups = sum(
        1
        for group in group_results
        if (
            group[
                "assessment_status"
            ]
            == "claimed_only"
        )
    )


    candidate_groups = sum(
        1
        for group in group_results
        if (
            group[
                "assessment_status"
            ]
            == "candidate"
        )
    )


    gap_groups = sum(
        1
        for group in group_results
        if (
            group[
                "assessment_status"
            ]
            == "gap"
        )
    )


    required_candidate_groups = sum(
        1
        for group in group_results
        if (
            group[
                "requirement_level"
            ]
            == "required"

            and
            group[
                "assessment_status"
            ]
            == "candidate"
        )
    )


    required_gap_groups = sum(
        1
        for group in group_results
        if (
            group[
                "requirement_level"
            ]
            == "required"

            and
            group[
                "assessment_status"
            ]
            == "gap"
        )
    )


    group_needs_review = sum(
        1
        for group in group_results
        if (
            group[
                "assessment_status"
            ]
            == "needs_review"
        )
    )


    unresolved_requirements = (
        len(
            unresolved
        )
        + group_needs_review
    )


    return {
        "total_concepts":
            total_concepts,

        "required_concepts":
            required_concepts,

        "preferred_concepts":
            preferred_concepts,

        "unknown_level_concepts":
            unknown_level_concepts,

        "evidenced_concepts":
            evidenced_concepts,

        "claimed_only_concepts":
            claimed_only_concepts,

        "candidate_concepts":
            candidate_concepts,

        "gap_concepts":
            gap_concepts,

        "required_candidate_concepts":
            required_candidate_concepts,

        "required_gap_concepts":
            required_gap_concepts,

        "unresolved_requirements":
            unresolved_requirements,

        "total_requirement_groups":
            total_groups,

        "required_requirement_groups":
            required_groups,

        "preferred_requirement_groups":
            preferred_groups,

        "unknown_requirement_groups":
            unknown_groups,

        "evidenced_requirement_groups":
            evidenced_groups,

        "claimed_only_requirement_groups":
            claimed_only_groups,

        "candidate_requirement_groups":
            candidate_groups,

        "gap_requirement_groups":
            gap_groups,

        "required_candidate_groups":
            required_candidate_groups,

        "required_gap_groups":
            required_gap_groups,
    }


def _upsert_summary(
    connection,
    profile_id,
    job_id,
    summary,
):
    connection.execute(
        text(
            """
            INSERT INTO
                job_profile_fit_summary (
                    profile_id,
                    job_id,
                    fit_version,

                    total_concepts,
                    required_concepts,
                    preferred_concepts,
                    unknown_level_concepts,

                    evidenced_concepts,
                    claimed_only_concepts,
                    candidate_concepts,
                    gap_concepts,

                    required_candidate_concepts,
                    required_gap_concepts,

                    unresolved_requirements,

                    total_requirement_groups,
                    required_requirement_groups,
                    preferred_requirement_groups,
                    unknown_requirement_groups,

                    evidenced_requirement_groups,
                    claimed_only_requirement_groups,
                    candidate_requirement_groups,
                    gap_requirement_groups,

                    required_candidate_groups,
                    required_gap_groups
                )

            VALUES (
                :profile_id,
                :job_id,
                :fit_version,

                :total_concepts,
                :required_concepts,
                :preferred_concepts,
                :unknown_level_concepts,

                :evidenced_concepts,
                :claimed_only_concepts,
                :candidate_concepts,
                :gap_concepts,

                :required_candidate_concepts,
                :required_gap_concepts,

                :unresolved_requirements,

                :total_requirement_groups,
                :required_requirement_groups,
                :preferred_requirement_groups,
                :unknown_requirement_groups,

                :evidenced_requirement_groups,
                :claimed_only_requirement_groups,
                :candidate_requirement_groups,
                :gap_requirement_groups,

                :required_candidate_groups,
                :required_gap_groups
            )

            ON CONFLICT (
                profile_id,
                job_id,
                fit_version
            )

            DO UPDATE SET
                total_concepts =
                    EXCLUDED.total_concepts,

                required_concepts =
                    EXCLUDED.required_concepts,

                preferred_concepts =
                    EXCLUDED.preferred_concepts,

                unknown_level_concepts =
                    EXCLUDED
                    .unknown_level_concepts,

                evidenced_concepts =
                    EXCLUDED
                    .evidenced_concepts,

                claimed_only_concepts =
                    EXCLUDED
                    .claimed_only_concepts,

                candidate_concepts =
                    EXCLUDED
                    .candidate_concepts,

                gap_concepts =
                    EXCLUDED.gap_concepts,

                required_candidate_concepts =
                    EXCLUDED
                    .required_candidate_concepts,

                required_gap_concepts =
                    EXCLUDED
                    .required_gap_concepts,

                unresolved_requirements =
                    EXCLUDED
                    .unresolved_requirements,

                total_requirement_groups =
                    EXCLUDED
                    .total_requirement_groups,

                required_requirement_groups =
                    EXCLUDED
                    .required_requirement_groups,

                preferred_requirement_groups =
                    EXCLUDED
                    .preferred_requirement_groups,

                unknown_requirement_groups =
                    EXCLUDED
                    .unknown_requirement_groups,

                evidenced_requirement_groups =
                    EXCLUDED
                    .evidenced_requirement_groups,

                claimed_only_requirement_groups =
                    EXCLUDED
                    .claimed_only_requirement_groups,

                candidate_requirement_groups =
                    EXCLUDED
                    .candidate_requirement_groups,

                gap_requirement_groups =
                    EXCLUDED
                    .gap_requirement_groups,

                required_candidate_groups =
                    EXCLUDED
                    .required_candidate_groups,

                required_gap_groups =
                    EXCLUDED
                    .required_gap_groups,

                assessed_at =
                    NOW();
            """
        ),
        {
            "profile_id":
                profile_id,

            "job_id":
                job_id,

            "fit_version":
                FIT_VERSION,

            **summary,
        },
    )


def _public_group(
    group,
):
    return {
        "requirement_mention_id":
            group[
                "requirement_mention_id"
            ],

        "type":
            group[
                "requirement_type"
            ],

        "level":
            group[
                "requirement_level"
            ],

        "text":
            group[
                "raw_text"
            ],

        "operator":
            group[
                "group_operator"
            ],

        "is_open":
            group[
                "group_is_open"
            ],

        "status":
            group[
                "assessment_status"
            ],

        "explanation":
            group[
                "explanation"
            ],

        "matched_concept_id":
            group[
                "matched_concept_id"
            ],

        "concepts": [
            {
                "concept_id":
                    member[
                        "concept_id"
                    ],

                "name":
                    member[
                        "canonical_name"
                    ],

                "type":
                    member[
                        "concept_type"
                    ],

                "claim_status":
                    member[
                        "claim_status"
                    ],

                "evidence_status":
                    member[
                        "evidence_status"
                    ],

                "fit_status":
                    member[
                        "fit_status"
                    ],
            }

            for member
            in group[
                "members"
            ]
        ],
    }


def assess_job_fit(
    profile_id,
    job_id,
    database_url=None,
):
    engine = create_database_engine(
        database_url
    )


    with engine.connect() as connection:

        job = _job_row(
            connection,
            job_id,
        )


        if job is None:

            raise ValueError(
                "Job not found."
            )


        if job[
            "insufficient_description"
        ]:

            return {
                "profile_available":
                    _profile_has_resume(
                        connection,
                        profile_id,
                    ),

                "job":
                    dict(
                        job
                    ),

                "profile_fit": {
                    "status":
                        "insufficient_job_data",

                    "model_version":
                        FIT_VERSION,

                    "reason":
                        (
                            "The available job "
                            "description does not "
                            "contain enough "
                            "information for a "
                            "reliable resume "
                            "comparison."
                        ),
                },
            }


        has_resume = (
            _profile_has_resume(
                connection,
                profile_id,
            )
        )


        if not has_resume:

            return {
                "profile_available":
                    False,

                "job":
                    dict(
                        job
                    ),

                "profile_fit": {
                    "status":
                        "no_resume",

                    "model_version":
                        FIT_VERSION,

                    "reason":
                        (
                            "Upload a resume "
                            "before comparing "
                            "this role with your "
                            "profile."
                        ),
                },
            }


        profile_status = (
            _profile_status(
                connection,
                profile_id,
            )
        )


        rows, unresolved = (
            _job_requirement_rows(
                connection,
                job_id,
            )
        )


    (
        concept_results,
        group_results,
    ) = _build_results(
        rows,
        profile_status,
    )


    summary = _summary_values(
        concept_results,
        group_results,
        unresolved,
    )


    with engine.begin() as connection:

        _persist_fit(
            connection,
            profile_id,
            job_id,
            concept_results,
            group_results,
            unresolved,
        )


        _upsert_summary(
            connection,
            profile_id,
            job_id,
            summary,
        )


    public_groups = [
        _public_group(
            group
        )

        for group
        in group_results
    ]


    unresolved_public = [
        {
            "requirement_mention_id":
                requirement[
                    "requirement_mention_id"
                ],

            "type":
                requirement[
                    "requirement_type"
                ],

            "level":
                requirement[
                    "requirement_level"
                ],

            "text":
                requirement[
                    "raw_text"
                ],

            "status":
                "needs_review",

            "explanation":
                (
                    "This requirement has "
                    "not yet been mapped to "
                    "an assessable profile "
                    "concept."
                ),
        }

        for requirement
        in unresolved
    ]


    return {
        "profile_available":
            True,

        "job":
            dict(
                job
            ),

        "profile_fit": {
            "status":
                "assessed",

            "model_version":
                FIT_VERSION,

            "summary":
                summary,

            "groups":
                public_groups,

            "unresolved_requirements":
                unresolved_public,
        },
    }
