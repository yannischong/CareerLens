import argparse
import os

from dotenv import load_dotenv

from src.analytics.skill_gap_analysis import (
    analyze_skill_gaps,
)


PRIORITY_TIER_ORDER = {
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 4,
}


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


def classify_priority(
    gap,
):
    """
    Classify one profile-support gap.

    These tiers deliberately avoid a
    fake numerical "importance score".

    A
        Repeated unsupported capability
        across multiple analyzed jobs.

    B
        Appears once, but explicitly
        marked required.

    C
        Appears once with unspecified
        requirement level.

    D
        Appears only as a preferred /
        advantageous requirement.
    """

    gap_job_count = (
        gap[
            "gap_job_count"
        ]
    )

    required = (
        gap[
            "required_gap_groups"
        ]
    )

    unknown = (
        gap[
            "unknown_gap_groups"
        ]
    )

    preferred = (
        gap[
            "preferred_gap_groups"
        ]
    )


    if gap_job_count >= 2:

        return {
            "priority_tier":
                "A",

            "priority_label":
                "Repeated profile gap",

            "priority_reason":
                (
                    "This unsupported "
                    "capability appears "
                    "across multiple "
                    "analyzed jobs."
                ),

            "next_step":
                "verify_or_strengthen",
        }


    if required > 0:

        return {
            "priority_tier":
                "B",

            "priority_label":
                "Required profile gap",

            "priority_reason":
                (
                    "This capability "
                    "appears in one "
                    "analyzed job and "
                    "is explicitly "
                    "marked required."
                ),

            "next_step":
                "verify_or_strengthen",
        }


    if unknown > 0:

        return {
            "priority_tier":
                "C",

            "priority_label":
                "Single-job signal",

            "priority_reason":
                (
                    "This unsupported "
                    "capability appears "
                    "in one analyzed "
                    "job, but its "
                    "requirement level "
                    "is unspecified."
                ),

            "next_step":
                "review",
        }


    if preferred > 0:

        return {
            "priority_tier":
                "D",

            "priority_label":
                "Preferred-only signal",

            "priority_reason":
                (
                    "This capability "
                    "appears only as a "
                    "preferred or "
                    "advantageous "
                    "requirement."
                ),

            "next_step":
                "optional",
        }


    return {
        "priority_tier":
            "C",

        "priority_label":
            "Single-job signal",

        "priority_reason":
            (
                "This unsupported "
                "capability appears "
                "in one analyzed job."
            ),

        "next_step":
            "review",
    }


def build_gap_priority(
    profile_id,
    search_request_id,
    database_url=None,
):
    analysis = analyze_skill_gaps(
        profile_id=
            profile_id,

        search_request_id=
            search_request_id,

        database_url=
            database_url,
    )


    analyzed_job_count = (
        analysis[
            "coverage"
        ][
            "analyzed_job_count"
        ]
    )


    priorities = []


    for gap in analysis[
        "skill_gap_families"
    ]:

        classification = (
            classify_priority(
                gap
            )
        )


        gap_job_share_pct = (
            percentage(
                gap[
                    "gap_job_count"
                ],
                analyzed_job_count,
            )
        )


        item = {
            **gap,

            **classification,

            "gap_job_share_pct":
                gap_job_share_pct,

            "profile_gap_interpretation":
                (
                    "No confirmed claim "
                    "or evidence currently "
                    "supports this "
                    "requirement. This "
                    "does not prove that "
                    "the user lacks the "
                    "capability."
                ),
        }


        priorities.append(
            item
        )


    # Deterministic ordering.
    #
    # We rank by tier first, then use
    # transparent observed evidence
    # rather than an arbitrary weighted
    # score.
    priorities.sort(
        key=lambda item: (
            PRIORITY_TIER_ORDER[
                item[
                    "priority_tier"
                ]
            ],

            -item[
                "gap_job_count"
            ],

            -item[
                "required_gap_groups"
            ],

            -item[
                "unknown_gap_groups"
            ],

            -item[
                "gap_weight"
            ],

            item[
                "family_name"
            ].casefold(),
        )
    )


    for index, item in enumerate(
        priorities,
        start=1,
    ):

        item[
            "priority_rank"
        ] = index


    tier_counts = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    }


    for item in priorities:

        tier_counts[
            item[
                "priority_tier"
            ]
        ] += 1


    return {
        "profile_id":
            profile_id,

        "search_request_id":
            search_request_id,

        "query_text":
            analysis[
                "query_text"
            ],

        "location_text":
            analysis[
                "location_text"
            ],

        "country_code":
            analysis[
                "country_code"
            ],

        "coverage":
            analysis[
                "coverage"
            ],

        "priority_method": {
            "type":
                "rule_based",

            "uses_numeric_importance_score":
                False,

            "tier_definitions": {
                "A":
                    (
                        "Repeated unsupported "
                        "capability across two "
                        "or more analyzed jobs."
                    ),

                "B":
                    (
                        "Single-job gap that "
                        "is explicitly required."
                    ),

                "C":
                    (
                        "Single-job gap with "
                        "unspecified requirement "
                        "level."
                    ),

                "D":
                    (
                        "Single-job gap appearing "
                        "only as preferred or "
                        "advantageous."
                    ),
            },
        },

        "tier_counts":
            tier_counts,

        "priority_count":
            len(
                priorities
            ),

        "priorities":
            priorities,

        # Preserve the underlying analysis
        # for API/UI transparency.
        "raw_skill_gaps":
            analysis[
                "raw_skill_gaps"
            ],
    }


if __name__ == "__main__":

    load_dotenv()


    parser = argparse.ArgumentParser(
        description=(
            "Build transparent "
            "CareerCompass profile-gap "
            "priorities."
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


    result = build_gap_priority(
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
        "Analyzed jobs:",
        (
            f"{coverage['analyzed_job_count']}"
            f" / "
            f"{coverage['total_search_jobs']}"
        ),
    )


    print(
        "Analyzed sufficiently "
        "described jobs:",
        (
            f"{coverage['analyzed_job_count']}"
            f" / "
            f"{coverage['sufficient_description_jobs']}"
        ),
    )


    print(
        "Overall coverage:",
        (
            f"{coverage[
                'overall_coverage_pct'
            ]}%"
        ),
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
        "PROFILE GAP PRIORITIES"
    )

    print(
        "=" * 100
    )


    for gap in result[
        "priorities"
    ]:

        print()

        print(
            f"{gap['priority_rank']}. "
            f"[Tier "
            f"{gap['priority_tier']}] "
            f"{gap['family_name']}"
        )


        print(
            "   classification:",
            gap[
                "priority_label"
            ],
        )


        print(
            "   gap jobs:",
            (
                f"{gap['gap_job_count']}"
                f" / "
                f"{coverage[
                    'analyzed_job_count'
                ]}"
                f" "
                f"({gap[
                    'gap_job_share_pct'
                ]}%)"
            ),
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


        if (
            len(
                gap[
                    "source_concepts"
                ]
            )
            > 1
        ):

            print(
                "   grouped concepts:",
                " | ".join(
                    gap[
                        "source_concepts"
                    ]
                ),
            )


        print(
            "   reason:",
            gap[
                "priority_reason"
            ],
        )


        print(
            "   next step:",
            gap[
                "next_step"
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