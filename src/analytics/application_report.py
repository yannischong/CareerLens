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
        "Show CareerCompass application analytics."
    )
)

parser.add_argument(
    "--profile-id",
    type=int,
    required=True,
)

args = parser.parse_args()


with engine.begin() as connection:

    summary = (
        connection.execute(
            text(
                """
                SELECT *
                FROM application_funnel_summary
                WHERE profile_id =
                    :profile_id;
                """
            ),
            {
                "profile_id":
                    args.profile_id,
            },
        )
        .mappings()
        .first()
    )


if summary is None:

    print(
        "No tracked opportunities "
        "for this profile."
    )

    raise SystemExit


print()
print("CAREERCOMPASS APPLICATION FUNNEL")
print("----------------------------")

print(
    f"Tracked: "
    f"{summary['tracked_opportunities']}"
)

print(
    f"Applied: "
    f"{summary['applications']}"
)

print(
    f"OA: "
    f"{summary['oa_reached']}"
)

print(
    f"Interview: "
    f"{summary['interviews_reached']}"
)

print(
    f"Offer: "
    f"{summary['offers_received']}"
)

print(
    f"Rejected: "
    f"{summary['rejections']}"
)


print()
print("CONVERSION")

print(
    f"Application → OA: "
    f"{summary['application_to_oa_pct']}"
    f"%"
)

print(
    f"Application → Interview: "
    f"{summary['application_to_interview_pct']}"
    f"%"
)

print(
    f"Application → Offer: "
    f"{summary['application_to_offer_pct']}"
    f"%"
)

print(
    f"Interview → Offer: "
    f"{summary['interview_to_offer_pct']}"
    f"%"
)


print()
print("RESPONSE TIME")

print(
    f"Average days to first response: "
    f"{summary['avg_days_to_first_response']}"
)

print(
    f"Average days to interview: "
    f"{summary['avg_days_to_interview']}"
)