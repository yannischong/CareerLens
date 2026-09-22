import argparse
import json

from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)


VALID_EVENT_TYPES = {
    "note",
    "deadline",
    "oa",
    "interview",
    "follow_up",
    "offer",
    "rejection",
    "withdrawal",
    "other",
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
    "--type",
    required=True,
)

parser.add_argument(
    "--notes",
)

parser.add_argument(
    "--event-at",
)

parser.add_argument(
    "--metadata",
    default="{}",
)

args = parser.parse_args()


if args.type not in VALID_EVENT_TYPES:

    raise ValueError(
        f"Invalid event type: "
        f"{args.type}"
    )


event_at = None

if args.event_at:

    event_at = datetime.fromisoformat(
        args.event_at
    )


metadata = json.loads(
    args.metadata
)


with engine.begin() as connection:

    connection.execute(
        text(
            """
            INSERT INTO opportunity_events (
                opportunity_id,
                event_type,
                event_at,
                notes,
                metadata,
                event_source
            )

            VALUES (
                :opportunity_id,
                :event_type,
                COALESCE(
                    :event_at,
                    NOW()
                ),
                :notes,
                CAST(:metadata AS JSONB),
                'manual'
            );
            """
        ),
        {
            "opportunity_id":
                args.opportunity_id,

            "event_type":
                args.type,

            "event_at":
                event_at,

            "notes":
                args.notes,

            "metadata":
                json.dumps(
                    metadata
                ),
        },
    )


print(
    "Opportunity event recorded."
)