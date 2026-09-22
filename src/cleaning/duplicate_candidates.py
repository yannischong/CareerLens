from rapidfuzz import fuzz

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)


TITLE_THRESHOLD = 85.0


load_dotenv()

engine = create_database_engine()


with engine.begin() as connection:

    candidate_pairs = (
        connection.execute(
            text(
                """
                SELECT
                    a.job_id
                        AS job_id_a,

                    b.job_id
                        AS job_id_b,

                    a.source
                        AS source_a,

                    b.source
                        AS source_b,

                    a.normalized_company_name
                        AS company_a,

                    b.normalized_company_name
                        AS company_b,

                    a.normalized_title
                        AS title_a,

                    b.normalized_title
                        AS title_b,

                    a.normalized_location
                        AS location_a,

                    b.normalized_location
                        AS location_b,

                    a.derived_posted_date
                        AS date_a,

                    b.derived_posted_date
                        AS date_b

                FROM jobs a

                JOIN jobs b
                    ON a.job_id < b.job_id

                WHERE
                    a.source <> b.source

                    AND
                    a.normalized_company_name
                    IS NOT NULL

                    AND
                    a.normalized_company_name =
                    b.normalized_company_name;
                """
            )
        )
        .mappings()
        .all()
    )


print(
    f"Checking "
    f"{len(candidate_pairs)} "
    f"cross-source candidate pairs..."
)


detected = 0


for pair in candidate_pairs:

    title_a = (
        pair["title_a"]
        or ""
    )

    title_b = (
        pair["title_b"]
        or ""
    )


    title_similarity = (
        fuzz.token_sort_ratio(
            title_a,
            title_b,
        )
    )


    if (
        title_similarity
        < TITLE_THRESHOLD
    ):
        continue


    location_a = (
        pair["location_a"]
    )

    location_b = (
        pair["location_b"]
    )


    if (
        location_a is None
        or location_b is None
    ):
        location_match = None

    else:
        location_match = (
            location_a
            == location_b
        )


    date_a = pair["date_a"]
    date_b = pair["date_b"]


    if (
        date_a is not None
        and date_b is not None
    ):
        date_gap_days = abs(
            (date_a - date_b).days
        )

    else:
        date_gap_days = None


    with engine.begin() as connection:

        connection.execute(
            text(
                """
                INSERT INTO duplicate_candidates (
                    job_id_a,
                    job_id_b,
                    company_similarity,
                    title_similarity,
                    location_match,
                    date_gap_days,
                    match_method
                )

                VALUES (
                    :job_id_a,
                    :job_id_b,
                    :company_similarity,
                    :title_similarity,
                    :location_match,
                    :date_gap_days,
                    :match_method
                )

                ON CONFLICT (
                    job_id_a,
                    job_id_b
                )

                DO UPDATE SET
                    company_similarity =
                        EXCLUDED.company_similarity,

                    title_similarity =
                        EXCLUDED.title_similarity,

                    location_match =
                        EXCLUDED.location_match,

                    date_gap_days =
                        EXCLUDED.date_gap_days,

                    match_method =
                        EXCLUDED.match_method,

                    detected_at =
                        NOW();
                """
            ),
            {
                "job_id_a":
                    pair["job_id_a"],

                "job_id_b":
                    pair["job_id_b"],

                "company_similarity":
                    100.0,

                "title_similarity":
                    title_similarity,

                "location_match":
                    location_match,

                "date_gap_days":
                    date_gap_days,

                "match_method":
                    "normalized_company_exact"
                    "+title_fuzzy",
            },
        )


    detected += 1


print(
    f"Detected "
    f"{detected} "
    f"duplicate candidates."
)