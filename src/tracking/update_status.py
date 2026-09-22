import argparse

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)


VALID_STATUSES = {
    "discovered",
    "saved",
    "to_apply",
    "applied",
    "oa",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
    "closed",
}


load_dotenv()

engine = create_database_engine()


parser = argparse.ArgumentParser()

parser.add_argument(
    "--opportunity-id",
    type=int,
    required=True,
)

parser.add_argument(
    "--status",
    required=True,
)

parser.add_argument(
    "--notes",
)

args = parser.parse_args()


if args.status not in VALID_STATUSES:

    raise ValueError(
        f"Invalid status: {args.status}"
    )


with engine.begin() as connection:

    opportunity = (
        connection.execute(
            text(
                """
                SELECT
                    opportunity_id,
                    current_status

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


    old_status = opportunity[
        "current_status"
    ]


    if old_status == args.status:

        print(
            f"Opportunity already has "
            f"status '{args.status}'."
        )

        raise SystemExit


    connection.execute(
        text(
            """
            UPDATE opportunities

            SET
                current_status =
                    :new_status,

                updated_at =
                    NOW()

            WHERE opportunity_id =
                :opportunity_id;
            """
        ),
        {
            "new_status":
                args.status,

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
                :old_status,
                :new_status,
                :notes,
                'manual'
            );
            """
        ),
        {
            "opportunity_id":
                args.opportunity_id,

            "old_status":
                old_status,

            "new_status":
                args.status,

            "notes":
                args.notes,
        },
    )


print(
    f"{old_status} -> "
    f"{args.status}"
)