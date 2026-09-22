import argparse

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)


load_dotenv()

engine = create_database_engine()


parser = argparse.ArgumentParser()

parser.add_argument(
    "--opportunity-id",
    type=int,
    required=True,
)

parser.add_argument(
    "--resume-id",
    type=int,
)

parser.add_argument(
    "--url",
)

parser.add_argument(
    "--method",
)

parser.add_argument(
    "--referral",
    action="store_true",
)

parser.add_argument(
    "--cover-letter",
    action="store_true",
)

parser.add_argument(
    "--notes",
)

args = parser.parse_args()


with engine.begin() as connection:

    opportunity = (
        connection.execute(
            text(
                """
                SELECT current_status
                FROM opportunities
                WHERE opportunity_id =
                    :opportunity_id;
                """
            ),
            {
                "opportunity_id":
                    args.opportunity_id,
            },
        )
        .mappings()
        .first()
    )


    if opportunity is None:

        raise ValueError(
            "Opportunity not found."
        )


    previous_status = opportunity[
        "current_status"
    ]


    application_id = (
        connection.execute(
            text(
                """
                INSERT INTO applications (
                    opportunity_id,
                    resume_id,
                    application_url,
                    application_method,
                    referral_used,
                    cover_letter_used,
                    notes
                )

                VALUES (
                    :opportunity_id,
                    :resume_id,
                    :application_url,
                    :application_method,
                    :referral_used,
                    :cover_letter_used,
                    :notes
                )

                ON CONFLICT (
                    opportunity_id
                )

                DO UPDATE SET
                    resume_id =
                        EXCLUDED.resume_id,

                    application_url =
                        EXCLUDED.application_url,

                    application_method =
                        EXCLUDED.application_method,

                    referral_used =
                        EXCLUDED.referral_used,

                    cover_letter_used =
                        EXCLUDED.cover_letter_used,

                    notes =
                        EXCLUDED.notes,

                    updated_at =
                        NOW()

                RETURNING application_id;
                """
            ),
            {
                "opportunity_id":
                    args.opportunity_id,

                "resume_id":
                    args.resume_id,

                "application_url":
                    args.url,

                "application_method":
                    args.method,

                "referral_used":
                    args.referral,

                "cover_letter_used":
                    args.cover_letter,

                "notes":
                    args.notes,
            },
        )
        .scalar_one()
    )


    if previous_status != "applied":

        connection.execute(
            text(
                """
                UPDATE opportunities

                SET
                    current_status =
                        'applied',

                    updated_at =
                        NOW()

                WHERE opportunity_id =
                    :opportunity_id;
                """
            ),
            {
                "opportunity_id":
                    args.opportunity_id,
            },
        )


        connection.execute(
            text(
                """
                INSERT INTO opportunity_events (
                    opportunity_id,
                    event_type,
                    from_status,
                    to_status,
                    notes,
                    event_source
                )

                VALUES (
                    :opportunity_id,
                    'status_change',
                    :from_status,
                    'applied',
                    'Application recorded',
                    'manual'
                );
                """
            ),
            {
                "opportunity_id":
                    args.opportunity_id,

                "from_status":
                    previous_status,
            },
        )


print(
    f"Application recorded: "
    f"{application_id}"
)