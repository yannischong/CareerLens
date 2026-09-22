import argparse

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)


load_dotenv()

engine = create_database_engine()


parser = argparse.ArgumentParser(
    description=(
        "Save a CareerCompass job "
        "as a tracked opportunity."
    )
)

parser.add_argument(
    "--profile-id",
    type=int,
    required=True,
)

parser.add_argument(
    "--job-id",
    type=int,
    required=True,
)

parser.add_argument(
    "--search-request-id",
    type=int,
)

parser.add_argument(
    "--priority",
    choices=[
        "low",
        "medium",
        "high",
    ],
    default="medium",
)

parser.add_argument(
    "--notes",
)

args = parser.parse_args()


with engine.begin() as connection:

    existing = (
        connection.execute(
            text(
                """
                SELECT
                    opportunity_id,
                    current_status

                FROM opportunities

                WHERE
                    profile_id =
                        :profile_id

                    AND job_id =
                        :job_id;
                """
            ),
            {
                "profile_id":
                    args.profile_id,

                "job_id":
                    args.job_id,
            },
        )
        .mappings()
        .first()
    )


    if existing:

        opportunity_id = (
            existing[
                "opportunity_id"
            ]
        )

        connection.execute(
            text(
                """
                UPDATE opportunities

                SET
                    priority = :priority,
                    notes = COALESCE(
                        :notes,
                        notes
                    ),
                    updated_at = NOW()

                WHERE opportunity_id =
                    :opportunity_id;
                """
            ),
            {
                "priority":
                    args.priority,

                "notes":
                    args.notes,

                "opportunity_id":
                    opportunity_id,
            },
        )

        print(
            f"Opportunity already exists: "
            f"{opportunity_id}"
        )

    else:

        opportunity_id = (
            connection.execute(
                text(
                    """
                    INSERT INTO opportunities (
                        profile_id,
                        job_id,
                        source_search_request_id,
                        current_status,
                        priority,
                        notes
                    )

                    VALUES (
                        :profile_id,
                        :job_id,
                        :search_request_id,
                        'saved',
                        :priority,
                        :notes
                    )

                    RETURNING opportunity_id;
                    """
                ),
                {
                    "profile_id":
                        args.profile_id,

                    "job_id":
                        args.job_id,

                    "search_request_id":
                        args.search_request_id,

                    "priority":
                        args.priority,

                    "notes":
                        args.notes,
                },
            )
            .scalar_one()
        )


        connection.execute(
            text(
                """
                INSERT INTO opportunity_events (
                    opportunity_id,
                    event_type,
                    from_status,
                    to_status,
                    event_source
                )

                VALUES (
                    :opportunity_id,
                    'created',
                    NULL,
                    'saved',
                    'manual'
                );
                """
            ),
            {
                "opportunity_id":
                    opportunity_id,
            },
        )


        print(
            f"Saved opportunity: "
            f"{opportunity_id}"
        )