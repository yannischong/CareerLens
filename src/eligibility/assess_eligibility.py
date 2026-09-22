import argparse

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)


ASSESSMENT_VERSION = (
    "eligibility_v1"
)

ELIGIBILITY_VERSION = (
    "job_eligibility_v1"
)


load_dotenv()


def evaluate_requirement(
    requirement,
    facts_by_type,
):
    operator = (
        requirement[
            "comparison_operator"
        ]
    )

    required_value = (
        requirement[
            "requirement_value"
        ]
    )

    fact_type = (
        requirement[
            "fact_type"
        ]
    )

    if operator == "manual_review":

        return (
            "needs_review",
            (
                "This requirement is "
                "not yet safe to assess "
                "automatically."
            ),
        )

    matching_facts = (
        facts_by_type.get(
            fact_type,
            [],
        )
    )

    if not matching_facts:

        return (
            "needs_review",
            (
                "No confirmed or candidate "
                "profile fact is available."
            ),
        )

    confirmed = [
        fact
        for fact in matching_facts
        if (
            fact[
                "review_status"
            ]
            == "confirmed"
        )
    ]

    candidates = [
        fact
        for fact in matching_facts
        if (
            fact[
                "review_status"
            ]
            == "candidate"
        )
    ]

    usable = (
        confirmed
        if confirmed
        else candidates
    )

    certainty = (
        "confirmed"
        if confirmed
        else "candidate"
    )

    if fact_type == "experience_years":

        required_years = float(
            required_value[
                "years"
            ]
        )

        max_years = max(
            float(
                fact[
                    "fact_value"
                ][
                    "years"
                ]
            )
            for fact in usable
        )

        passed = (
            max_years
            >= required_years
        )

    elif fact_type == "education_level":

        required_rank = int(
            required_value[
                "rank"
            ]
        )

        max_rank = max(
            int(
                fact[
                    "fact_value"
                ][
                    "rank"
                ]
            )
            for fact in usable
        )

        passed = (
            max_rank
            >= required_rank
        )

    elif fact_type == "graduation_year":

        years = [
            int(
                fact[
                    "fact_value"
                ][
                    "year"
                ]
            )
            for fact in usable
        ]

        if operator == "eq":

            passed = (
                int(
                    required_value[
                        "year"
                    ]
                )
                in years
            )

        elif operator == "between":

            minimum = int(
                required_value[
                    "min_year"
                ]
            )

            maximum = int(
                required_value[
                    "max_year"
                ]
            )

            passed = any(
                minimum
                <= year
                <= maximum

                for year in years
            )

        else:

            return (
                "needs_review",
                (
                    "Unsupported "
                    "graduation year "
                    "comparison."
                ),
            )

    elif fact_type == "language":

        required_language = (
            required_value[
                "language"
            ]
            .casefold()
        )

        passed = any(
            fact[
                "fact_value"
            ]
            .get(
                "language",
                "",
            )
            .casefold()
            ==
            required_language

            for fact in usable
        )

    elif fact_type == "security_clearance":

        passed = any(
            bool(
                fact[
                    "fact_value"
                ].get(
                    "has_clearance"
                )
            )
            for fact in usable
        )

    else:

        return (
            "needs_review",
            (
                "Automatic comparison is "
                "not implemented for this "
                "requirement type."
            ),
        )

    if passed:

        if certainty == "confirmed":

            return (
                "satisfied",
                (
                    "A confirmed profile fact "
                    "satisfies the requirement."
                ),
            )

        return (
            "candidate",
            (
                "A resume-extracted candidate "
                "fact appears to satisfy the "
                "requirement but has not "
                "been confirmed."
            ),
        )

    if certainty == "confirmed":

        return (
            "not_satisfied",
            (
                "Confirmed profile information "
                "does not satisfy the "
                "requirement."
            ),
        )

    return (
        "needs_review",
        (
            "Candidate profile information "
            "does not establish eligibility."
        ),
    )


def assess_eligibility(
    profile_id,
    search_request_id,
    database_url=None,
):
    engine = create_database_engine(
        database_url
    )

    with engine.connect() as connection:

        facts = (
            connection.execute(
                text(
                    """
                    SELECT
                        fact_type,
                        fact_value,
                        review_status

                    FROM
                        profile_eligibility_facts

                    WHERE
                        profile_id =
                            :profile_id

                        AND
                        review_status IN (
                            'confirmed',
                            'candidate'
                        );
                    """
                ),
                {
                    "profile_id":
                        profile_id,
                },
            )
            .mappings()
            .all()
        )

    facts_by_type = {}

    for fact in facts:

        facts_by_type.setdefault(
            fact[
                "fact_type"
            ],
            [],
        ).append(
            fact
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

                    JOIN source_search_results result
                        ON
                            j.job_id =
                            result.job_id

                    JOIN source_search_runs run
                        ON
                            result.source_search_run_id =
                            run.source_search_run_id

                    WHERE
                        run.search_request_id =
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
            "No jobs found for this search request."
        )

    summaries = []

    for job in jobs:

        with engine.connect() as connection:

            requirements = (
                connection.execute(
                    text(
                        """
                        SELECT
                            e.eligibility_requirement_id,
                            e.fact_type,
                            e.comparison_operator,
                            e.requirement_value

                        FROM
                            job_eligibility_requirements e

                        JOIN job_requirement_mentions r
                            ON
                                e.requirement_mention_id =
                                r.requirement_mention_id

                        WHERE
                            r.job_id =
                                :job_id

                            AND
                            e.extractor_version =
                                :extractor_version;
                        """
                    ),
                    {
                        "job_id":
                            job[
                                "job_id"
                            ],

                        "extractor_version":
                            ELIGIBILITY_VERSION,
                    },
                )
                .mappings()
                .all()
            )

        counts = {
            "satisfied": 0,
            "candidate": 0,
            "not_satisfied": 0,
            "needs_review": 0,
        }

        with engine.begin() as connection:

            for requirement in requirements:

                status, explanation = (
                    evaluate_requirement(
                        requirement,
                        facts_by_type,
                    )
                )

                counts[
                    status
                ] += 1

                connection.execute(
                    text(
                        """
                        INSERT INTO
                            job_profile_eligibility_checks (
                                profile_id,
                                eligibility_requirement_id,
                                assessment_status,
                                explanation,
                                assessment_version
                            )

                        VALUES (
                            :profile_id,
                            :eligibility_requirement_id,
                            :assessment_status,
                            :explanation,
                            :assessment_version
                        )

                        ON CONFLICT (
                            profile_id,
                            eligibility_requirement_id,
                            assessment_version
                        )

                        DO UPDATE SET
                            assessment_status =
                                EXCLUDED.assessment_status,

                            explanation =
                                EXCLUDED.explanation,

                            assessed_at =
                                NOW();
                        """
                    ),
                    {
                        "profile_id":
                            profile_id,

                        "eligibility_requirement_id":
                            requirement[
                                "eligibility_requirement_id"
                            ],

                        "assessment_status":
                            status,

                        "explanation":
                            explanation,

                        "assessment_version":
                            ASSESSMENT_VERSION,
                    },
                )

            connection.execute(
                text(
                    """
                    INSERT INTO
                        job_profile_eligibility_summary (
                            profile_id,
                            job_id,
                            assessment_version,
                            total_requirements,
                            satisfied_requirements,
                            candidate_requirements,
                            not_satisfied_requirements,
                            needs_review_requirements
                        )

                    VALUES (
                        :profile_id,
                        :job_id,
                        :assessment_version,
                        :total,
                        :satisfied,
                        :candidate,
                        :not_satisfied,
                        :needs_review
                    )

                    ON CONFLICT (
                        profile_id,
                        job_id,
                        assessment_version
                    )

                    DO UPDATE SET
                        total_requirements =
                            EXCLUDED.total_requirements,

                        satisfied_requirements =
                            EXCLUDED.satisfied_requirements,

                        candidate_requirements =
                            EXCLUDED.candidate_requirements,

                        not_satisfied_requirements =
                            EXCLUDED
                            .not_satisfied_requirements,

                        needs_review_requirements =
                            EXCLUDED
                            .needs_review_requirements,

                        assessed_at =
                            NOW();
                    """
                ),
                {
                    "profile_id":
                        profile_id,

                    "job_id":
                        job[
                            "job_id"
                        ],

                    "assessment_version":
                        ASSESSMENT_VERSION,

                    "total":
                        len(
                            requirements
                        ),

                    "satisfied":
                        counts[
                            "satisfied"
                        ],

                    "candidate":
                        counts[
                            "candidate"
                        ],

                    "not_satisfied":
                        counts[
                            "not_satisfied"
                        ],

                    "needs_review":
                        counts[
                            "needs_review"
                        ],
                },
            )

        summaries.append(
            {
                "job_id":
                    job[
                        "job_id"
                    ],

                "raw_title":
                    job[
                        "raw_title"
                    ],

                "total":
                    len(
                        requirements
                    ),

                **counts,
            }
        )

    return {
        "profile_id":
            profile_id,

        "search_request_id":
            search_request_id,

        "jobs_assessed":
            len(
                summaries
            ),

        "jobs":
            summaries,
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

    result = assess_eligibility(
        profile_id=
            args.profile_id,

        search_request_id=
            args.search_request_id,
    )

    print(
        f"Assessed "
        f"{result['jobs_assessed']} "
        f"jobs."
    )

    print(
        "Eligibility assessment complete."
    )