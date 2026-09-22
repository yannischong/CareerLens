import argparse
from collections import defaultdict

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)


FIT_VERSION = (
    "profile_fit_v2"
)

REQUIREMENT_VERSION = (
    "requirements_v2"
)

CONCEPT_VERSION = (
    "atomic_concepts_v2"
)

MAPPER_VERSION = (
    "profile_concepts_v2"
)


load_dotenv()


STATUS_STRENGTH = {
    "gap": 0,
    "candidate": 1,
    "claimed_only": 2,
    "evidenced": 3,
}


def get_direct_fit_status(
    concept_id,
    profile_status,
):
    statuses = profile_status.get(
        concept_id,
        {
            "claim_status":
                "none",

            "evidence_status":
                "none",
        },
    )


    claim_status = (
        statuses[
            "claim_status"
        ]
    )

    evidence_status = (
        statuses[
            "evidence_status"
        ]
    )


    if (
        evidence_status
        == "confirmed"
    ):
        fit_status = (
            "evidenced"
        )

    elif (
        claim_status
        == "confirmed"
    ):
        fit_status = (
            "claimed_only"
        )

    elif (
        evidence_status
        == "candidate"

        or
        claim_status
        == "candidate"
    ):
        fit_status = (
            "candidate"
        )

    else:
        fit_status = (
            "gap"
        )


    return {
        "claim_status":
            claim_status,

        "evidence_status":
            evidence_status,

        "fit_status":
            fit_status,
    }


def assess_group(
    group,
):
    members = (
        group["members"]
    )


    if not members:

        return {
            "assessment_status":
                "needs_review",

            "matched_concept_id":
                None,

            "explanation":
                (
                    "No assessable concepts "
                    "were extracted from this "
                    "requirement."
                ),
        }


    operator = (
        group[
            "group_operator"
        ]
    )


    if operator == "any_of":

        best_member = max(
            members,
            key=lambda member:
                STATUS_STRENGTH[
                    member[
                        "fit_status"
                    ]
                ],
        )


        best_status = (
            best_member[
                "fit_status"
            ]
        )


        if (
            best_status == "gap"
            and group[
                "group_is_open"
            ]
        ):

            return {
                "assessment_status":
                    "needs_review",

                "matched_concept_id":
                    None,

                "explanation":
                    (
                        "None of the listed "
                        "alternatives matched, "
                        "but this requirement "
                        "contains an open-ended "
                        "alternative such as "
                        "'related', 'similar', "
                        "or 'equivalent'."
                    ),
            }


        if best_status == "gap":

            return {
                "assessment_status":
                    "gap",

                "matched_concept_id":
                    None,

                "explanation":
                    (
                        "None of the listed "
                        "alternatives matched "
                        "the current profile."
                    ),
            }


        return {
            "assessment_status":
                best_status,

            "matched_concept_id":
                best_member[
                    "concept_id"
                ],

            "explanation":
                (
                    "At least one acceptable "
                    "alternative matched the "
                    "current profile."
                ),
        }


    weakest_member = min(
        members,
        key=lambda member:
            STATUS_STRENGTH[
                member[
                    "fit_status"
                ]
            ],
    )


    weakest_status = (
        weakest_member[
            "fit_status"
        ]
    )


    return {
        "assessment_status":
            weakest_status,

        "matched_concept_id":
            (
                weakest_member[
                    "concept_id"
                ]

                if len(members) == 1

                else None
            ),

        "explanation":
            (
                "All concepts in this "
                "requirement are treated as "
                "joint requirements. The "
                "group status reflects the "
                "weakest concept match."
            ),
    }


def assess_profile_fit(
    profile_id,
    search_request_id,
    database_url=None,
):
    engine = create_database_engine(
        database_url
    )


    with engine.connect() as connection:

        profile = (
            connection.execute(
                text(
                    """
                    SELECT
                        profile_id,
                        profile_name

                    FROM user_profiles

                    WHERE
                        profile_id =
                            :profile_id;
                    """
                ),
                {
                    "profile_id":
                        profile_id,
                },
            )
            .mappings()
            .one_or_none()
        )


    if profile is None:

        raise ValueError(
            "Profile not found."
        )


    with engine.connect() as connection:

        jobs = (
            connection.execute(
                text(
                    """
                    SELECT DISTINCT
                        j.job_id,
                        j.raw_title

                    FROM jobs j

                    JOIN source_search_results
                        ssres

                        ON
                            j.job_id =
                            ssres.job_id

                    JOIN source_search_runs
                        ssr

                        ON
                            ssres.source_search_run_id =
                            ssr.source_search_run_id

                    WHERE
                        ssr.search_request_id =
                            :search_request_id

                    ORDER BY
                        j.job_id;
                    """
                ),
                {
                    "search_request_id":
                        search_request_id,
                },
            )
            .mappings()
            .all()
        )


    if not jobs:

        raise ValueError(
            "No jobs found for this "
            "search request."
        )


    with engine.connect() as connection:

        profile_status_rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        concept_id,
                        claim_status,
                        evidence_status

                    FROM profile_concept_status

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


    profile_status = {
        row["concept_id"]: {
            "claim_status":
                row["claim_status"],

            "evidence_status":
                row["evidence_status"],
        }

        for row in profile_status_rows
    }


    job_summaries = []


    for job in jobs:

        job_id = (
            job["job_id"]
        )


        with engine.connect() as connection:

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
                            job_requirement_concepts
                            jrc

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
                                    job_requirement_concepts
                                    jrc

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


        groups = {}


        concept_results_by_id = {}


        for row in rows:

            mention_id = (
                row[
                    "requirement_mention_id"
                ]
            )


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


            concept_id = (
                member[
                    "concept_id"
                ]
            )


            existing = (
                concept_results_by_id.get(
                    concept_id
                )
            )


            level_strength = {
                "unknown": 1,
                "preferred": 2,
                "required": 3,
            }


            if (
                existing is None

                or
                level_strength[
                    row[
                        "requirement_level"
                    ]
                ]
                >
                level_strength[
                    existing[
                        "requirement_level"
                    ]
                ]
            ):

                concept_results_by_id[
                    concept_id
                ] = {
                    **member,

                    "requirement_level":
                        row[
                            "requirement_level"
                        ],
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


        concept_results = list(
            concept_results_by_id.values()
        )


        with engine.begin() as connection:

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


        total_needs_review = (
            len(unresolved)
            + group_needs_review
        )


        with engine.begin() as connection:

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
                            EXCLUDED
                            .gap_concepts,

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
                        total_needs_review,

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
                },
            )


        job_summaries.append(
            {
                "job_id":
                    job_id,

                "raw_title":
                    job[
                        "raw_title"
                    ],

                "total_groups":
                    total_groups,

                "evidenced":
                    evidenced_groups,

                "claimed_only":
                    claimed_only_groups,

                "candidate":
                    candidate_groups,

                "gaps":
                    gap_groups,

                "required_gaps":
                    required_gap_groups,

                "needs_review":
                    total_needs_review,
            }
        )


    return {
        "profile_id":
            profile_id,

        "search_request_id":
            search_request_id,

        "fit_version":
            FIT_VERSION,

        "jobs_assessed":
            len(
                job_summaries
            ),

        "jobs":
            job_summaries,
    }


if __name__ == "__main__":

    parser = argparse.ArgumentParser()


    parser.add_argument(
        "--profile-id",
        type=int,
        required=True,
    )


    parser.add_argument(
        "--search-request-id",
        type=int,
        required=True,
    )


    args = parser.parse_args()


    result = assess_profile_fit(
        profile_id=
            args.profile_id,

        search_request_id=
            args.search_request_id,
    )


    print(
        f"Assessed "
        f"{result['jobs_assessed']} "
        f"jobs using "
        f"{FIT_VERSION}."
    )