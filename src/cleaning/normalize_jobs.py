import argparse
import json

from dotenv import load_dotenv
from sqlalchemy import text

from src.cleaning.normalization import (
    derive_posted_date,
    normalize_company_name,
    normalize_description,
    normalize_location,
    normalize_title,
)
from src.cleaning.quality import (
    build_quality_flags,
)
from src.collection.database import (
    create_database_engine,
)


NORMALIZATION_VERSION = "normalize_v1"


load_dotenv()


def normalize_jobs(
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
                raw_title,
                raw_company_name,
                location_raw,
                description,
                date_posted,
                first_seen_at,
                source_metadata
            FROM jobs
            ORDER BY job_id;
        """

        parameters = {}

    else:
        query = """
            SELECT DISTINCT
                j.job_id,
                j.raw_title,
                j.raw_company_name,
                j.location_raw,
                j.description,
                j.date_posted,
                j.first_seen_at,
                j.source_metadata

            FROM jobs AS j

            JOIN source_search_results AS ssres
                ON j.job_id =
                   ssres.job_id

            JOIN source_search_runs AS ssr
                ON ssres.source_search_run_id =
                   ssr.source_search_run_id

            WHERE
                ssr.search_request_id =
                    :search_request_id

            ORDER BY j.job_id;
        """

        parameters = {
            "search_request_id":
                search_request_id,
        }

    with engine.connect() as connection:
        jobs = connection.execute(
            text(query),
            parameters,
        ).mappings().all()

    print(
        f"Normalizing {len(jobs)} jobs..."
    )

    for job in jobs:
        normalized_title = normalize_title(
            job["raw_title"]
        )

        normalized_company = (
            normalize_company_name(
                job["raw_company_name"]
            )
        )

        normalized_location = (
            normalize_location(
                job["location_raw"]
            )
        )

        normalized_description = (
            normalize_description(
                job["description"]
            )
        )

        derived_date, date_method = (
            derive_posted_date(
                job["date_posted"],
                job["source_metadata"],
                job["first_seen_at"],
            )
        )

        quality_flags = (
            build_quality_flags(job)
        )

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE jobs

                    SET
                        normalized_title =
                            :normalized_title,

                        normalized_company_name =
                            :normalized_company,

                        normalized_location =
                            :normalized_location,

                        normalized_description =
                            :normalized_description,

                        derived_posted_date =
                            :derived_posted_date,

                        derived_posted_date_method =
                            :date_method,

                        normalization_version =
                            :normalization_version,

                        normalized_at =
                            NOW()

                    WHERE job_id =
                        :job_id;
                    """
                ),
                {
                    "normalized_title":
                        normalized_title,

                    "normalized_company":
                        normalized_company,

                    "normalized_location":
                        normalized_location,

                    "normalized_description":
                        normalized_description,

                    "derived_posted_date":
                        derived_date,

                    "date_method":
                        date_method,

                    "normalization_version":
                        NORMALIZATION_VERSION,

                    "job_id":
                        job["job_id"],
                },
            )

            connection.execute(
                text(
                    """
                    DELETE FROM job_quality_flags

                    WHERE
                        job_id = :job_id

                        AND generated_by =
                            :generated_by;
                    """
                ),
                {
                    "job_id":
                        job["job_id"],

                    "generated_by":
                        NORMALIZATION_VERSION,
                },
            )

            for (
                flag_code,
                details,
            ) in quality_flags:

                connection.execute(
                    text(
                        """
                        INSERT INTO
                            job_quality_flags (
                                job_id,
                                flag_code,
                                details,
                                generated_by
                            )

                        VALUES (
                            :job_id,
                            :flag_code,

                            CAST(
                                :details
                                AS JSONB
                            ),

                            :generated_by
                        )

                        ON CONFLICT (
                            job_id,
                            flag_code,
                            generated_by
                        )

                        DO UPDATE SET
                            details =
                                EXCLUDED.details,

                            created_at =
                                NOW();
                        """
                    ),
                    {
                        "job_id":
                            job["job_id"],

                        "flag_code":
                            flag_code,

                        "details":
                            json.dumps(
                                details
                            ),

                        "generated_by":
                            NORMALIZATION_VERSION,
                    },
                )

    print(
        "Normalization complete."
    )

    return len(jobs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Normalize CareerCompass jobs "
            "and generate quality flags."
        )
    )

    parser.add_argument(
        "--search-request-id",
        type=int,
        required=False,
    )

    args = parser.parse_args()

    normalize_jobs(
        search_request_id=
            args.search_request_id
    )