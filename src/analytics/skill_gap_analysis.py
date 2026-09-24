import argparse
import os

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)
from src.taxonomy.atomic import (
    normalize_concept,
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

PROFILE_MAPPER_VERSION = (
    "profile_concepts_v2"
)


DEVELOPMENT_CONCEPT_TYPES = {
    "skill",
    "tool",
    "domain_knowledge",
    "hard_skill",
    "soft_skill",
}


# Only merge concepts when the
# equivalence is strong enough that we
# are comfortable treating them as one
# development area.
#
# Do NOT broadly cluster merely because
# two skills are semantically related.
CONCEPT_FAMILIES = {
    "Problem solving": {
        "analytical and problem-solving",
        "analytical and problem solving",
        "problem-solving",
        "problem solving",
        "solve problems",
    },

    "Stakeholder management": {
        "stakeholder engagement",
        "stakeholder management and collaboration",
    },
}


FAMILY_LOOKUP = {}


for (
    family_name,
    aliases,
) in CONCEPT_FAMILIES.items():

    for alias in aliases:

        FAMILY_LOOKUP[
            normalize_concept(
                alias
            )
        ] = family_name


def atomic_profile_status(
    claim_status,
    evidence_status,
):
    if evidence_status == "confirmed":
        return "evidenced"


    if claim_status == "confirmed":
        return "claimed_only"


    if (
        evidence_status == "candidate"

        or

        claim_status == "candidate"
    ):
        return "candidate"


    return "unsupported"


def concept_family_name(
    canonical_name,
):
    normalized = normalize_concept(
        canonical_name
    )


    return FAMILY_LOOKUP.get(
        normalized,
        canonical_name,
    )


def percentage(
    numerator,
    denominator,
):
    if denominator == 0:
        return 0.0


    return round(
        (
            numerator
            /
            denominator
        )
        * 100,
        1,
    )


def analyze_skill_gaps(
    profile_id,
    search_request_id,
    database_url=None,
):
    engine = create_database_engine(
        database_url
    )


    with engine.connect() as connection:

        search = (
            connection.execute(
                text(
                    """
                    SELECT
                        search_request_id,
                        query_text,
                        location_text,
                        country_code

                    FROM search_requests

                    WHERE
                        search_request_id =
                            :search_request_id;
                    """
                ),
                {
                    "search_request_id":
                        search_request_id,
                },
            )
            .mappings()
            .one_or_none()
        )


        if search is None:

            raise ValueError(
                "Search request not found."
            )


        quality_summary = (
            connection.execute(
                text(
                    """
                    WITH search_jobs AS (
                        SELECT DISTINCT
                            job_id

                        FROM
                            job_relevance_scores

                        WHERE
                            search_request_id =
                                :search_request_id
                    )

                    SELECT
                        COUNT(*)
                            AS total_jobs,

                        COUNT(*) FILTER (
                            WHERE NOT EXISTS (
                                SELECT 1

                                FROM
                                    job_quality_flags qf

                                WHERE
                                    qf.job_id =
                                        sj.job_id

                                    AND
                                    qf.flag_code =
                                        'insufficient_description'
                            )
                        )
                            AS sufficient_description_jobs,

                        COUNT(*) FILTER (
                            WHERE EXISTS (
                                SELECT 1

                                FROM
                                    job_quality_flags qf

                                WHERE
                                    qf.job_id =
                                        sj.job_id

                                    AND
                                    qf.flag_code =
                                        'insufficient_description'
                            )
                        )
                            AS insufficient_description_jobs

                    FROM
                        search_jobs sj;
                    """
                ),
                {
                    "search_request_id":
                        search_request_id,
                },
            )
            .mappings()
            .one()
        )


        rows = (
            connection.execute(
                text(
                    """
                    WITH search_jobs AS (
                        SELECT DISTINCT
                            jrs.job_id,

                            EXISTS (
                                SELECT 1

                                FROM
                                    job_quality_flags qf

                                WHERE
                                    qf.job_id =
                                        jrs.job_id

                                    AND
                                    qf.flag_code =
                                        'insufficient_description'
                            )
                                AS insufficient_description

                        FROM
                            job_relevance_scores jrs

                        WHERE
                            jrs.search_request_id =
                                :search_request_id
                    ),

                    group_members AS (
                        SELECT
                            r.job_id,

                            j.raw_title,

                            sj.insufficient_description,

                            r.requirement_mention_id,

                            r.requirement_type,

                            r.requirement_level,

                            r.raw_text
                                AS requirement_text,

                            gf.group_operator,

                            gf.group_is_open,

                            gf.assessment_status
                                AS group_status,

                            jrc.concept_id,

                            c.canonical_name,

                            c.concept_type,

                            pcs.claim_status,

                            pcs.evidence_status,

                            COUNT(*) OVER (
                                PARTITION BY
                                    r.requirement_mention_id
                            )
                                AS group_member_count

                        FROM
                            search_jobs sj

                        JOIN
                            job_requirement_mentions r

                            ON
                                r.job_id =
                                sj.job_id

                        JOIN
                            jobs j

                            ON
                                j.job_id =
                                r.job_id

                        JOIN
                            job_profile_requirement_group_fit gf

                            ON
                                gf.requirement_mention_id =
                                r.requirement_mention_id

                                AND
                                gf.profile_id =
                                    :profile_id

                                AND
                                gf.fit_version =
                                    :fit_version

                        JOIN
                            job_requirement_concepts jrc

                            ON
                                jrc.requirement_mention_id =
                                r.requirement_mention_id

                                AND
                                jrc.extractor_version =
                                    :concept_version

                        JOIN
                            requirement_concepts c

                            ON
                                c.concept_id =
                                jrc.concept_id

                        LEFT JOIN
                            profile_concept_status pcs

                            ON
                                pcs.profile_id =
                                :profile_id

                                AND
                                pcs.concept_id =
                                c.concept_id

                                AND
                                pcs.mapper_version =
                                    :mapper_version

                        WHERE
                            r.extractor_version =
                                :requirement_version
                    )

                    SELECT
                        *

                    FROM
                        group_members

                    ORDER BY
                        job_id,
                        requirement_mention_id,
                        canonical_name;
                    """
                ),
                {
                    "profile_id":
                        profile_id,

                    "search_request_id":
                        search_request_id,

                    "fit_version":
                        FIT_VERSION,

                    "requirement_version":
                        REQUIREMENT_VERSION,

                    "concept_version":
                        CONCEPT_VERSION,

                    "mapper_version":
                        PROFILE_MAPPER_VERSION,
                },
            )
            .mappings()
            .all()
        )


    total_search_jobs = int(
        quality_summary[
            "total_jobs"
        ]
    )

    sufficient_description_jobs = int(
        quality_summary[
            "sufficient_description_jobs"
        ]
    )

    insufficient_description_jobs = int(
        quality_summary[
            "insufficient_description_jobs"
        ]
    )


    all_jobs_with_groups = set()

    analyzed_jobs = set()

    excluded_low_quality_jobs = set()

    analyzed_groups = set()

    gap_groups = set()

    review_groups = set()

    concept_stats = {}


    for row in rows:

        job_id = row[
            "job_id"
        ]

        mention_id = row[
            "requirement_mention_id"
        ]

        concept_id = row[
            "concept_id"
        ]

        group_key = (
            job_id,
            mention_id,
        )


        all_jobs_with_groups.add(
            job_id
        )


        # Requirement extraction may
        # still produce something from a
        # short provider snippet.
        #
        # That information can remain in
        # the job-level UI, but it should
        # not drive cross-market skill
        # development recommendations.
        if row[
            "insufficient_description"
        ]:

            excluded_low_quality_jobs.add(
                job_id
            )

            continue


        analyzed_jobs.add(
            job_id
        )

        analyzed_groups.add(
            group_key
        )


        group_status = row[
            "group_status"
        ]


        if group_status == "gap":

            gap_groups.add(
                group_key
            )


        elif (
            group_status
            == "needs_review"
        ):

            review_groups.add(
                group_key
            )


        concept_type = row[
            "concept_type"
        ]


        if (
            concept_type
            not in
            DEVELOPMENT_CONCEPT_TYPES
        ):

            continue


        if (
            concept_id
            not in concept_stats
        ):

            concept_stats[
                concept_id
            ] = {
                "concept_id":
                    concept_id,

                "canonical_name":
                    row[
                        "canonical_name"
                    ],

                "concept_type":
                    concept_type,

                "job_ids":
                    set(),

                "group_ids":
                    set(),

                "gap_job_ids":
                    set(),

                "gap_group_ids":
                    set(),

                "required_gap_group_ids":
                    set(),

                "preferred_gap_group_ids":
                    set(),

                "unknown_gap_group_ids":
                    set(),

                "all_of_gap_group_ids":
                    set(),

                "alternative_gap_group_ids":
                    set(),

                "needs_review_group_ids":
                    set(),

                "evidenced_group_ids":
                    set(),

                "claimed_only_group_ids":
                    set(),

                "candidate_group_ids":
                    set(),

                "gap_weight":
                    0.0,

                "examples":
                    [],
            }


        stats = concept_stats[
            concept_id
        ]


        stats[
            "job_ids"
        ].add(
            job_id
        )


        stats[
            "group_ids"
        ].add(
            group_key
        )


        if (
            group_status
            == "needs_review"
        ):

            stats[
                "needs_review_group_ids"
            ].add(
                group_key
            )


        elif (
            group_status
            == "evidenced"
        ):

            stats[
                "evidenced_group_ids"
            ].add(
                group_key
            )


        elif (
            group_status
            == "claimed_only"
        ):

            stats[
                "claimed_only_group_ids"
            ].add(
                group_key
            )


        elif (
            group_status
            == "candidate"
        ):

            stats[
                "candidate_group_ids"
            ].add(
                group_key
            )


        if group_status != "gap":
            continue


        atomic_status = (
            atomic_profile_status(
                claim_status=
                    row[
                        "claim_status"
                    ],

                evidence_status=
                    row[
                        "evidence_status"
                    ],
            )
        )


        # Even inside a logical ALL_OF
        # gap, some individual members
        # may already be supported.
        #
        # Only the unsupported atomic
        # concepts become development
        # gaps.
        if (
            atomic_status
            != "unsupported"
        ):

            continue


        group_operator = row[
            "group_operator"
        ]


        if (
            group_operator
            == "any_of"
        ):

            member_count = max(
                int(
                    row[
                        "group_member_count"
                    ]
                ),
                1,
            )

            contribution = (
                1.0
                /
                member_count
            )

            stats[
                "alternative_gap_group_ids"
            ].add(
                group_key
            )


        else:

            contribution = 1.0

            stats[
                "all_of_gap_group_ids"
            ].add(
                group_key
            )


        stats[
            "gap_weight"
        ] += contribution


        stats[
            "gap_job_ids"
        ].add(
            job_id
        )


        stats[
            "gap_group_ids"
        ].add(
            group_key
        )


        requirement_level = row[
            "requirement_level"
        ]


        if (
            requirement_level
            == "required"
        ):

            stats[
                "required_gap_group_ids"
            ].add(
                group_key
            )


        elif (
            requirement_level
            == "preferred"
        ):

            stats[
                "preferred_gap_group_ids"
            ].add(
                group_key
            )


        else:

            stats[
                "unknown_gap_group_ids"
            ].add(
                group_key
            )


        example_key = (
            job_id,
            mention_id,
        )


        existing_example_keys = {
            (
                example[
                    "job_id"
                ],
                example[
                    "requirement_mention_id"
                ],
            )

            for example
            in stats[
                "examples"
            ]
        }


        if (
            example_key
            not in
            existing_example_keys

            and

            len(
                stats[
                    "examples"
                ]
            )
            < 5
        ):

            stats[
                "examples"
            ].append(
                {
                    "job_id":
                        job_id,

                    "raw_title":
                        row[
                            "raw_title"
                        ],

                    "requirement_mention_id":
                        mention_id,

                    "requirement_level":
                        requirement_level,

                    "group_operator":
                        group_operator,

                    "group_is_open":
                        row[
                            "group_is_open"
                        ],

                    "requirement_text":
                        row[
                            "requirement_text"
                        ],
                }
            )


    raw_skill_gaps = []


    for stats in concept_stats.values():

        if not stats[
            "gap_group_ids"
        ]:
            continue


        raw_skill_gaps.append(
            {
                "concept_id":
                    stats[
                        "concept_id"
                    ],

                "canonical_name":
                    stats[
                        "canonical_name"
                    ],

                "concept_type":
                    stats[
                        "concept_type"
                    ],

                "jobs_requiring":
                    len(
                        stats[
                            "job_ids"
                        ]
                    ),

                "groups_requiring":
                    len(
                        stats[
                            "group_ids"
                        ]
                    ),

                "gap_job_count":
                    len(
                        stats[
                            "gap_job_ids"
                        ]
                    ),

                "gap_group_count":
                    len(
                        stats[
                            "gap_group_ids"
                        ]
                    ),

                "gap_weight":
                    round(
                        stats[
                            "gap_weight"
                        ],
                        4,
                    ),

                "required_gap_groups":
                    len(
                        stats[
                            "required_gap_group_ids"
                        ]
                    ),

                "preferred_gap_groups":
                    len(
                        stats[
                            "preferred_gap_group_ids"
                        ]
                    ),

                "unknown_gap_groups":
                    len(
                        stats[
                            "unknown_gap_group_ids"
                        ]
                    ),

                "all_of_gap_groups":
                    len(
                        stats[
                            "all_of_gap_group_ids"
                        ]
                    ),

                "alternative_gap_groups":
                    len(
                        stats[
                            "alternative_gap_group_ids"
                        ]
                    ),

                "needs_review_groups":
                    len(
                        stats[
                            "needs_review_group_ids"
                        ]
                    ),

                "evidenced_groups":
                    len(
                        stats[
                            "evidenced_group_ids"
                        ]
                    ),

                "claimed_only_groups":
                    len(
                        stats[
                            "claimed_only_group_ids"
                        ]
                    ),

                "candidate_groups":
                    len(
                        stats[
                            "candidate_group_ids"
                        ]
                    ),

                "examples":
                    stats[
                        "examples"
                    ],
            }
        )


    raw_skill_gaps.sort(
        key=lambda item: (
            -item[
                "gap_weight"
            ],

            -item[
                "gap_job_count"
            ],

            -item[
                "required_gap_groups"
            ],

            item[
                "canonical_name"
            ].casefold(),
        )
    )


    # -------------------------------------------------
    # CONCEPT FAMILY AGGREGATION
    # -------------------------------------------------

    family_stats = {}


    for concept_id, stats in (
        concept_stats.items()
    ):

        if not stats[
            "gap_group_ids"
        ]:
            continue


        family_name = (
            concept_family_name(
                stats[
                    "canonical_name"
                ]
            )
        )


        if (
            family_name
            not in family_stats
        ):

            family_stats[
                family_name
            ] = {
                "family_name":
                    family_name,

                "concept_ids":
                    set(),

                "source_concepts":
                    set(),

                "concept_types":
                    set(),

                "job_ids":
                    set(),

                "group_ids":
                    set(),

                "gap_job_ids":
                    set(),

                "gap_group_ids":
                    set(),

                "required_gap_group_ids":
                    set(),

                "preferred_gap_group_ids":
                    set(),

                "unknown_gap_group_ids":
                    set(),

                "all_of_gap_group_ids":
                    set(),

                "alternative_gap_group_ids":
                    set(),

                "group_gap_weights":
                    {},

                "examples":
                    [],
            }


        family = family_stats[
            family_name
        ]


        family[
            "concept_ids"
        ].add(
            concept_id
        )


        family[
            "source_concepts"
        ].add(
            stats[
                "canonical_name"
            ]
        )


        family[
            "concept_types"
        ].add(
            stats[
                "concept_type"
            ]
        )


        family[
            "job_ids"
        ].update(
            stats[
                "job_ids"
            ]
        )


        family[
            "group_ids"
        ].update(
            stats[
                "group_ids"
            ]
        )


        family[
            "gap_job_ids"
        ].update(
            stats[
                "gap_job_ids"
            ]
        )


        family[
            "gap_group_ids"
        ].update(
            stats[
                "gap_group_ids"
            ]
        )


        family[
            "required_gap_group_ids"
        ].update(
            stats[
                "required_gap_group_ids"
            ]
        )


        family[
            "preferred_gap_group_ids"
        ].update(
            stats[
                "preferred_gap_group_ids"
            ]
        )


        family[
            "unknown_gap_group_ids"
        ].update(
            stats[
                "unknown_gap_group_ids"
            ]
        )


        family[
            "all_of_gap_group_ids"
        ].update(
            stats[
                "all_of_gap_group_ids"
            ]
        )


        family[
            "alternative_gap_group_ids"
        ].update(
            stats[
                "alternative_gap_group_ids"
            ]
        )


        # Keep a family from being
        # inflated merely because two
        # synonymous concepts happened
        # to occur inside the same
        # logical requirement group.
        for group_key in stats[
            "gap_group_ids"
        ]:

            if (
                group_key
                in
                stats[
                    "alternative_gap_group_ids"
                ]
            ):

                matching_examples = [
                    example

                    for example
                    in stats[
                        "examples"
                    ]

                    if (
                        example[
                            "job_id"
                        ],
                        example[
                            "requirement_mention_id"
                        ],
                    )
                    == group_key
                ]


                member_weight = 0.0


                if matching_examples:

                    # The atomic concept's
                    # exact contribution is
                    # already represented in
                    # total gap_weight, but
                    # not stored per group.
                    #
                    # Reconstruct the logical
                    # alternative contribution
                    # from the examples only
                    # when possible.
                    member_count = sum(
                        1

                        for other_stats
                        in concept_stats.values()

                        if (
                            group_key
                            in
                            other_stats[
                                "gap_group_ids"
                            ]

                            and
                            group_key
                            in
                            other_stats[
                                "alternative_gap_group_ids"
                            ]
                        )
                    )


                    if member_count > 0:

                        member_weight = (
                            1.0
                            /
                            member_count
                        )


                existing_weight = (
                    family[
                        "group_gap_weights"
                    ].get(
                        group_key,
                        0.0,
                    )
                )


                family[
                    "group_gap_weights"
                ][
                    group_key
                ] = min(
                    1.0,
                    existing_weight
                    +
                    member_weight,
                )


            else:

                family[
                    "group_gap_weights"
                ][
                    group_key
                ] = 1.0


        existing_example_keys = {
            (
                example[
                    "job_id"
                ],
                example[
                    "requirement_mention_id"
                ],
            )

            for example
            in family[
                "examples"
            ]
        }


        for example in stats[
            "examples"
        ]:

            example_key = (
                example[
                    "job_id"
                ],
                example[
                    "requirement_mention_id"
                ],
            )


            if (
                example_key
                in
                existing_example_keys
            ):
                continue


            if (
                len(
                    family[
                        "examples"
                    ]
                )
                >= 5
            ):
                break


            family[
                "examples"
            ].append(
                example
            )

            existing_example_keys.add(
                example_key
            )


    skill_gap_families = []


    for family in (
        family_stats.values()
    ):

        family_gap_weight = sum(
            family[
                "group_gap_weights"
            ].values()
        )


        skill_gap_families.append(
            {
                "family_name":
                    family[
                        "family_name"
                    ],

                "concept_ids":
                    sorted(
                        family[
                            "concept_ids"
                        ]
                    ),

                "source_concepts":
                    sorted(
                        family[
                            "source_concepts"
                        ],
                        key=str.casefold,
                    ),

                "concept_types":
                    sorted(
                        family[
                            "concept_types"
                        ]
                    ),

                "jobs_requiring":
                    len(
                        family[
                            "job_ids"
                        ]
                    ),

                "groups_requiring":
                    len(
                        family[
                            "group_ids"
                        ]
                    ),

                "gap_job_count":
                    len(
                        family[
                            "gap_job_ids"
                        ]
                    ),

                "gap_group_count":
                    len(
                        family[
                            "gap_group_ids"
                        ]
                    ),

                "gap_weight":
                    round(
                        family_gap_weight,
                        4,
                    ),

                "required_gap_groups":
                    len(
                        family[
                            "required_gap_group_ids"
                        ]
                    ),

                "preferred_gap_groups":
                    len(
                        family[
                            "preferred_gap_group_ids"
                        ]
                    ),

                "unknown_gap_groups":
                    len(
                        family[
                            "unknown_gap_group_ids"
                        ]
                    ),

                "all_of_gap_groups":
                    len(
                        family[
                            "all_of_gap_group_ids"
                        ]
                    ),

                "alternative_gap_groups":
                    len(
                        family[
                            "alternative_gap_group_ids"
                        ]
                    ),

                "examples":
                    family[
                        "examples"
                    ],
            }
        )


    skill_gap_families.sort(
        key=lambda item: (
            -item[
                "gap_weight"
            ],

            -item[
                "gap_job_count"
            ],

            -item[
                "required_gap_groups"
            ],

            item[
                "family_name"
            ].casefold(),
        )
    )


    analyzed_job_count = len(
        analyzed_jobs
    )


    return {
        "profile_id":
            profile_id,

        "search_request_id":
            search_request_id,

        "query_text":
            search[
                "query_text"
            ],

        "location_text":
            search[
                "location_text"
            ],

        "country_code":
            search[
                "country_code"
            ],

        "fit_version":
            FIT_VERSION,

        "concept_version":
            CONCEPT_VERSION,

        "profile_mapper_version":
            PROFILE_MAPPER_VERSION,

        "coverage": {
            "total_search_jobs":
                total_search_jobs,

            "sufficient_description_jobs":
                sufficient_description_jobs,

            "insufficient_description_jobs":
                insufficient_description_jobs,

            "jobs_with_requirement_groups":
                len(
                    all_jobs_with_groups
                ),

            "analyzed_job_count":
                analyzed_job_count,

            "excluded_low_quality_jobs":
                len(
                    excluded_low_quality_jobs
                ),

            "overall_coverage_pct":
                percentage(
                    analyzed_job_count,
                    total_search_jobs,
                ),

            "sufficient_description_coverage_pct":
                percentage(
                    analyzed_job_count,
                    sufficient_description_jobs,
                ),
        },

        "requirement_group_count":
            len(
                analyzed_groups
            ),

        "gap_group_count":
            len(
                gap_groups
            ),

        "needs_review_group_count":
            len(
                review_groups
            ),

        "raw_skill_gap_count":
            len(
                raw_skill_gaps
            ),

        "skill_gap_family_count":
            len(
                skill_gap_families
            ),

        "skill_gap_families":
            skill_gap_families,

        "raw_skill_gaps":
            raw_skill_gaps,
    }


if __name__ == "__main__":

    load_dotenv()


    parser = argparse.ArgumentParser(
        description=(
            "Aggregate CareerCompass skill "
            "gaps across one search."
        )
    )


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


    result = analyze_skill_gaps(
        profile_id=
            args.profile_id,

        search_request_id=
            args.search_request_id,

        database_url=
            os.getenv(
                "SUPABASE_DATABASE_URL"
            ),
    )


    coverage = result[
        "coverage"
    ]


    print()
    print(
        "Search:",
        result[
            "query_text"
        ],
    )


    print()
    print(
        "COVERAGE"
    )

    print(
        "=" * 100
    )


    print(
        "Search jobs:",
        coverage[
            "total_search_jobs"
        ],
    )


    print(
        "Sufficient descriptions:",
        coverage[
            "sufficient_description_jobs"
        ],
    )


    print(
        "Insufficient descriptions:",
        coverage[
            "insufficient_description_jobs"
        ],
    )


    print(
        "Jobs with requirement groups:",
        coverage[
            "jobs_with_requirement_groups"
        ],
    )


    print(
        "Jobs used for gap intelligence:",
        coverage[
            "analyzed_job_count"
        ],
    )


    print(
        "Excluded low-quality jobs:",
        coverage[
            "excluded_low_quality_jobs"
        ],
    )


    print(
        "Overall search coverage:",
        f"{coverage['overall_coverage_pct']}%",
    )


    print(
        "Coverage among sufficient "
        "descriptions:",
        (
            f"{coverage[
                'sufficient_description_coverage_pct'
            ]}%"
        ),
    )


    print()
    print(
        "Requirement groups:",
        result[
            "requirement_group_count"
        ],
    )


    print(
        "Gap groups:",
        result[
            "gap_group_count"
        ],
    )


    print(
        "Needs review groups:",
        result[
            "needs_review_group_count"
        ],
    )


    print()
    print(
        "SKILL GAP FAMILIES"
    )

    print(
        "=" * 100
    )


    for index, gap in enumerate(
        result[
            "skill_gap_families"
        ],
        start=1,
    ):

        print()

        print(
            f"{index}. "
            f"{gap['family_name']}"
        )


        if (
            len(
                gap[
                    "source_concepts"
                ]
            )
            > 1
        ):

            print(
                "   concepts:",
                " | ".join(
                    gap[
                        "source_concepts"
                    ]
                ),
            )


        print(
            "   gap jobs:",
            gap[
                "gap_job_count"
            ],
        )


        print(
            "   logical gap weight:",
            gap[
                "gap_weight"
            ],
        )


        print(
            "   required / "
            "preferred / unknown:",
            gap[
                "required_gap_groups"
            ],
            "/",
            gap[
                "preferred_gap_groups"
            ],
            "/",
            gap[
                "unknown_gap_groups"
            ],
        )


        for example in gap[
            "examples"
        ][:2]:

            print(
                "   -",
                example[
                    "raw_title"
                ],
            )

            print(
                "     ",
                example[
                    "requirement_text"
                ],
            )