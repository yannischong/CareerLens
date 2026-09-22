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
    "--profile-id",
    type=int,
    required=True,
)

args = parser.parse_args()


with engine.begin() as connection:

    opportunities = (
        connection.execute(
            text(
                """
                SELECT
                    o.opportunity_id,
                    o.current_status,
                    o.priority,
                    j.raw_title,
                    j.raw_company_name

                FROM opportunities o

                JOIN jobs j
                    ON o.job_id =
                       j.job_id

                WHERE
                    o.profile_id =
                        :profile_id

                ORDER BY
                    CASE o.current_status

                        WHEN 'offer'
                            THEN 1

                        WHEN 'interview'
                            THEN 2

                        WHEN 'oa'
                            THEN 3

                        WHEN 'applied'
                            THEN 4

                        WHEN 'to_apply'
                            THEN 5

                        WHEN 'saved'
                            THEN 6

                        WHEN 'discovered'
                            THEN 7

                        ELSE 8

                    END,

                    o.updated_at DESC;
                """
            ),
            {
                "profile_id":
                    args.profile_id,
            },
        )
        .mappings()
        .all()
    )


if not opportunities:

    print(
        "No tracked opportunities."
    )

    raise SystemExit


for opportunity in opportunities:

    print(
        f"[{opportunity['current_status'].upper()}] "
        f"{opportunity['raw_title']} "
        f"@ "
        f"{opportunity['raw_company_name']} "
        f"| priority="
        f"{opportunity['priority']} "
        f"| id="
        f"{opportunity['opportunity_id']}"
    )