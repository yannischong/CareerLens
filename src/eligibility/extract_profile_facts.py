import argparse
import json

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)
from src.eligibility.rules import (
    extract_education_level,
    extract_profile_graduation_year,
)


PROFILE_FACT_VERSION = (
    "profile_eligibility_v1"
)


load_dotenv()


def extract_profile_facts(
    profile_id,
    database_url=None,
):
    engine = create_database_engine(
        database_url
    )

    with engine.connect() as connection:

        profile = (
            connection.execute(
                text(
                    """
                    SELECT
                        profile_id

                    FROM user_profiles

                    WHERE
                        profile_id =
                            :profile_id;
                    """
                ),
                {
                    "profile_id":
                        profile_id,
                },
            )
            .mappings()
            .one_or_none()
        )

        if profile is None:
            raise ValueError(
                "Profile not found."
            )

        education_items = (
            connection.execute(
                text(
                    """
                    SELECT
                        evidence_id,
                        raw_text

                    FROM profile_evidence

                    WHERE
                        profile_id =
                            :profile_id

                        AND
                        evidence_type =
                            'education';
                    """
                ),
                {
                    "profile_id":
                        profile_id,
                },
            )
            .mappings()
            .all()
        )

        language_claims = (
            connection.execute(
                text(
                    """
                    SELECT
                        claim_id,
                        raw_text

                    FROM profile_claims

                    WHERE
                        profile_id =
                            :profile_id

                        AND
                        claim_type =
                            'languages';
                    """
                ),
                {
                    "profile_id":
                        profile_id,
                },
            )
            .mappings()
            .all()
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                DELETE FROM
                    profile_eligibility_facts

                WHERE
                    profile_id =
                        :profile_id

                    AND
                    source_type =
                        'resume_extracted'

                    AND
                    extractor_version =
                        :extractor_version;
                """
            ),
            {
                "profile_id":
                    profile_id,

                "extractor_version":
                    PROFILE_FACT_VERSION,
            },
        )

    created = 0

    for item in education_items:

        education = (
            extract_education_level(
                item["raw_text"]
            )
        )

        if education:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        INSERT INTO
                            profile_eligibility_facts (
                                profile_id,
                                fact_type,
                                fact_value,
                                raw_text,
                                source_type,
                                review_status,
                                extractor_version
                            )

                        VALUES (
                            :profile_id,
                            'education_level',
                            CAST(
                                :fact_value
                                AS JSONB
                            ),
                            :raw_text,
                            'resume_extracted',
                            'candidate',
                            :extractor_version
                        );
                        """
                    ),
                    {
                        "profile_id":
                            profile_id,

                        "fact_value":
                            json.dumps(
                                education
                            ),

                        "raw_text":
                            item[
                                "raw_text"
                            ],

                        "extractor_version":
                            PROFILE_FACT_VERSION,
                    },
                )

                created += 1

        graduation_year = (
            extract_profile_graduation_year(
                item["raw_text"]
            )
        )

        if graduation_year:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        INSERT INTO
                            profile_eligibility_facts (
                                profile_id,
                                fact_type,
                                fact_value,
                                raw_text,
                                source_type,
                                review_status,
                                extractor_version
                            )

                        VALUES (
                            :profile_id,
                            'graduation_year',
                            CAST(
                                :fact_value
                                AS JSONB
                            ),
                            :raw_text,
                            'resume_extracted',
                            'candidate',
                            :extractor_version
                        );
                        """
                    ),
                    {
                        "profile_id":
                            profile_id,

                        "fact_value":
                            json.dumps(
                                {
                                    "year":
                                        graduation_year
                                }
                            ),

                        "raw_text":
                            item[
                                "raw_text"
                            ],

                        "extractor_version":
                            PROFILE_FACT_VERSION,
                    },
                )

                created += 1

    for claim in language_claims:

        language = (
            claim["raw_text"]
            .strip()
            .casefold()
        )

        if not language:
            continue

        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    INSERT INTO
                        profile_eligibility_facts (
                            profile_id,
                            fact_type,
                            fact_value,
                            raw_text,
                            source_type,
                            review_status,
                            extractor_version
                        )

                    VALUES (
                        :profile_id,
                        'language',
                        CAST(
                            :fact_value
                            AS JSONB
                        ),
                        :raw_text,
                        'resume_extracted',
                        'candidate',
                        :extractor_version
                    );
                    """
                ),
                {
                    "profile_id":
                        profile_id,

                    "fact_value":
                        json.dumps(
                            {
                                "language":
                                    language
                            }
                        ),

                    "raw_text":
                        claim[
                            "raw_text"
                        ],

                    "extractor_version":
                        PROFILE_FACT_VERSION,
                },
            )

            created += 1

    return {
        "profile_id":
            profile_id,

        "facts_created":
            created,
    }


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--profile-id",
        type=int,
        required=True,
    )

    args = parser.parse_args()

    result = extract_profile_facts(
        profile_id=
            args.profile_id
    )

    print(
        f"Created "
        f"{result['facts_created']} "
        f"candidate profile "
        f"eligibility facts."
    )