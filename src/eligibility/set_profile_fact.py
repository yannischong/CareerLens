import argparse
import json

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)


load_dotenv()

engine = create_database_engine()


parser = argparse.ArgumentParser(
    description=(
        "Add a user-confirmed eligibility "
        "fact to a CareerCompass profile."
    )
)

parser.add_argument(
    "--profile-id",
    type=int,
    required=True,
)

parser.add_argument(
    "--fact-type",
    required=True,
)

parser.add_argument(
    "--value",
    required=True,
    help="JSON object",
)

args = parser.parse_args()


fact_value = json.loads(
    args.value
)


with engine.begin() as connection:

    connection.execute(
        text(
            """
            INSERT INTO
                profile_eligibility_facts (
                    profile_id,
                    fact_type,
                    fact_value,
                    source_type,
                    review_status,
                    extractor_version
                )

            VALUES (
                :profile_id,
                :fact_type,
                CAST(:fact_value AS JSONB),
                'manual',
                'confirmed',
                NULL
            );
            """
        ),
        {
            "profile_id":
                args.profile_id,

            "fact_type":
                args.fact_type,

            "fact_value":
                json.dumps(
                    fact_value
                ),
        },
    )


print(
    "Confirmed profile fact added."
)