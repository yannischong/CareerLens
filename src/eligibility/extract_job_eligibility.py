import argparse
import json

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)
from src.eligibility.rules import (
    extract_education_level,
    extract_graduation_requirement,
    extract_languages,
)


REQUIREMENT_VERSION = "requirements_v2"
ELIGIBILITY_VERSION = "job_eligibility_v1"


load_dotenv()


def extract_job_eligibility(
    database_url=None,
    search_request_id=None,
):
    engine = create_database_engine(
        database_url
    )

    with engine.connect() as connection:

        if search_request_id is None:

            mentions = (
                connection.execute(
                    text(
                        """
                        SELECT
                            requirement_mention_id,
                            requirement_type,
                            raw_text,
                            structured_value

                        FROM job_requirement_mentions

                        WHERE
                            extractor_version =
                                :extractor_version

                        ORDER BY
                            requirement_mention_id;
                        """
                    ),
                    {
                        "extractor_version":
                            REQUIREMENT_VERSION,
                    },
                )
                .mappings()
                .all()
            )

        else:

            mentions = (
                connection.execute(
                    text(
                        """
                        SELECT DISTINCT
                            m.requirement_mention_id,
                            m.requirement_type,
                            m.raw_text,
                            m.structured_value

                        FROM
                            job_requirement_mentions m

                        JOIN source_search_results r
                            ON m.job_id =
                               r.job_id

                        JOIN source_search_runs sr
                            ON
                                r.source_search_run_id =
                                sr.source_search_run_id

                        WHERE
                            m.extractor_version =
                                :extractor_version

                            AND
                            sr.search_request_id =
                                :search_request_id

                        ORDER BY
                            m.requirement_mention_id;
                        """
                    ),
                    {
                        "extractor_version":
                            REQUIREMENT_VERSION,

                        "search_request_id":
                            search_request_id,
                    },
                )
                .mappings()
                .all()
            )

    created = 0

    for mention in mentions:

        requirement_type = (
            mention["requirement_type"]
        )

        raw_text = (
            mention["raw_text"]
        )

        requirements = []

        if requirement_type == "experience":

            structured = (
                mention["structured_value"]
                or {}
            )

            min_years = (
                structured.get(
                    "min_years"
                )
            )

            if min_years is not None:

                requirements.append(
                    (
                        "experience_years",
                        "gte",
                        {
                            "years":
                                float(
                                    min_years
                                )
                        },
                    )
                )

            else:

                requirements.append(
                    (
                        "experience",
                        "manual_review",
                        {},
                    )
                )

        elif requirement_type == "education":

            education = (
                extract_education_level(
                    raw_text
                )
            )

            if education:

                requirements.append(
                    (
                        "education_level",
                        "gte",
                        education,
                    )
                )

            else:

                requirements.append(
                    (
                        "education",
                        "manual_review",
                        {},
                    )
                )

            graduation = (
                extract_graduation_requirement(
                    raw_text
                )
            )

            if graduation:

                operator, value = (
                    graduation
                )

                requirements.append(
                    (
                        "graduation_year",
                        operator,
                        value,
                    )
                )

        elif requirement_type == "language":

            languages = (
                extract_languages(
                    raw_text
                )
            )

            if languages:

                for language in languages:

                    requirements.append(
                        (
                            "language",
                            "eq",
                            {
                                "language":
                                    language
                            },
                        )
                    )

            else:

                requirements.append(
                    (
                        "language",
                        "manual_review",
                        {},
                    )
                )

        elif requirement_type in {
            "work_authorization",
            "availability",
            "licence",
            "professional_registration",
        }:

            requirements.append(
                (
                    requirement_type,
                    "manual_review",
                    {},
                )
            )

        elif requirement_type == "security_clearance":

            requirements.append(
                (
                    "security_clearance",
                    "boolean",
                    {
                        "required": True
                    },
                )
            )

        else:
            continue

        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    DELETE FROM
                        job_eligibility_requirements

                    WHERE
                        requirement_mention_id =
                            :requirement_mention_id

                        AND
                        extractor_version =
                            :extractor_version;
                    """
                ),
                {
                    "requirement_mention_id":
                        mention[
                            "requirement_mention_id"
                        ],

                    "extractor_version":
                        ELIGIBILITY_VERSION,
                },
            )

            for (
                fact_type,
                operator,
                value,
            ) in requirements:

                connection.execute(
                    text(
                        """
                        INSERT INTO
                            job_eligibility_requirements (
                                requirement_mention_id,
                                fact_type,
                                comparison_operator,
                                requirement_value,
                                extractor_version
                            )

                        VALUES (
                            :requirement_mention_id,
                            :fact_type,
                            :comparison_operator,
                            CAST(
                                :requirement_value
                                AS JSONB
                            ),
                            :extractor_version
                        );
                        """
                    ),
                    {
                        "requirement_mention_id":
                            mention[
                                "requirement_mention_id"
                            ],

                        "fact_type":
                            fact_type,

                        "comparison_operator":
                            operator,

                        "requirement_value":
                            json.dumps(
                                value
                            ),

                        "extractor_version":
                            ELIGIBILITY_VERSION,
                    },
                )

                created += 1

    return {
        "mentions_processed":
            len(mentions),

        "eligibility_requirements":
            created,
    }


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--search-request-id",
        type=int,
        required=False,
    )

    args = parser.parse_args()

    result = extract_job_eligibility(
        search_request_id=
            args.search_request_id
    )

    print(
        f"Processed "
        f"{result['mentions_processed']} "
        f"requirement mentions."
    )

    print(
        f"Created "
        f"{result['eligibility_requirements']} "
        f"eligibility requirements."
    )