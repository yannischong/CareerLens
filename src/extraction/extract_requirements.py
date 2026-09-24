import argparse
import json

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)
from src.extraction.rules import (
    extract_requirements as extract_requirements_from_text,
)


EXTRACTOR_VERSION = "requirements_v2"


SOURCE_FIELDS = [
    "description",
    "requirements_text",
    "education_requirements",
    "experience_requirements",
]


load_dotenv()


def extract_job_requirements(
    database_url=None,
    search_request_id=None,
):
    engine = create_database_engine(
        database_url
    )

    if search_request_id is None:
        query = """
            SELECT
                job_id,
                description,
                requirements_text,
                education_requirements,
                experience_requirements

            FROM jobs

            ORDER BY job_id;
        """

        parameters = {}

    else:
        query = """
            SELECT DISTINCT
                j.job_id,
                j.description,
                j.requirements_text,
                j.education_requirements,
                j.experience_requirements

            FROM jobs AS j

            JOIN source_search_results AS ssres
                ON
                    j.job_id =
                    ssres.job_id

            JOIN source_search_runs AS ssr
                ON
                    ssres.source_search_run_id =
                    ssr.source_search_run_id

            WHERE
                ssr.search_request_id =
                    :search_request_id

            ORDER BY
                j.job_id;
        """

        parameters = {
            "search_request_id":
                search_request_id,
        }

    with engine.connect() as connection:
        jobs = (
            connection.execute(
                text(query),
                parameters,
            )
            .mappings()
            .all()
        )

    print(
        f"Extracting requirements "
        f"from {len(jobs)} jobs..."
    )

    total_mentions = 0

    for job in jobs:

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    DELETE FROM
                        job_requirement_mentions

                    WHERE
                        job_id =
                            :job_id

                        AND extractor_version =
                            :extractor_version;
                    """
                ),
                {
                    "job_id":
                        job["job_id"],

                    "extractor_version":
                        EXTRACTOR_VERSION,
                },
            )

        for source_field in SOURCE_FIELDS:

            source_text = job[
                source_field
            ]

            if not source_text:
                continue

            mentions = (
                extract_requirements_from_text(
                    source_text,
                    source_field=source_field,
                )
            )

            with engine.begin() as connection:

                for mention in mentions:

                    connection.execute(
                        text(
                            """
                            INSERT INTO
                                job_requirement_mentions (
                                    job_id,
                                    source_field,
                                    requirement_type,
                                    requirement_level,
                                    raw_text,
                                    normalized_text,
                                    structured_value,
                                    rule_name,
                                    extractor_version
                                )

                            VALUES (
                                :job_id,
                                :source_field,
                                :requirement_type,
                                :requirement_level,
                                :raw_text,
                                :normalized_text,

                                CAST(
                                    :structured_value
                                    AS JSONB
                                ),

                                :rule_name,
                                :extractor_version
                            )

                            ON CONFLICT (
                                job_id,
                                source_field,
                                requirement_type,
                                normalized_text,
                                extractor_version
                            )

                            DO UPDATE SET
                                requirement_level =
                                    EXCLUDED.requirement_level,

                                raw_text =
                                    EXCLUDED.raw_text,

                                structured_value =
                                    EXCLUDED.structured_value,

                                rule_name =
                                    EXCLUDED.rule_name,

                                extracted_at =
                                    NOW();
                            """
                        ),
                        {
                            "job_id":
                                job["job_id"],

                            "source_field":
                                source_field,

                            "requirement_type":
                                mention.requirement_type,

                            "requirement_level":
                                mention.requirement_level,

                            "raw_text":
                                mention.raw_text,

                            "normalized_text":
                                mention.normalized_text,

                            "structured_value":
                                json.dumps(
                                    mention.structured_value
                                ),

                            "rule_name":
                                mention.rule_name,

                            "extractor_version":
                                EXTRACTOR_VERSION,
                        },
                    )

            total_mentions += len(
                mentions
            )

    print(
        f"Stored {total_mentions} "
        f"requirement mentions."
    )

    return {
        "jobs_processed":
            len(jobs),

        "mentions_stored":
            total_mentions,
    }


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Extract structured job "
            "requirements."
        )
    )

    parser.add_argument(
        "--search-request-id",
        type=int,
        required=False,
    )

    args = parser.parse_args()

    extract_job_requirements(
        search_request_id=
            args.search_request_id
    )