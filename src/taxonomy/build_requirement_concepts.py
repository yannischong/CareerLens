import argparse

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)
from src.taxonomy.atomic import (
    extract_atomic_concepts,
)


CONCEPT_EXTRACTOR_VERSION = (
    "atomic_concepts_v2"
)

REQUIREMENT_VERSION = (
    "requirements_v2"
)


load_dotenv()


def build_requirement_concepts(
    database_url=None,
    search_request_id=None,
):
    engine = create_database_engine(
        database_url
    )


    if search_request_id is None:

        query = """
            SELECT
                requirement_mention_id,
                requirement_type,
                raw_text,
                structured_value

            FROM job_requirement_mentions

            WHERE
                extractor_version =
                    :extractor_version

            ORDER BY
                requirement_mention_id;
        """

        parameters = {
            "extractor_version":
                REQUIREMENT_VERSION,
        }

    else:

        query = """
            SELECT DISTINCT
                m.requirement_mention_id,
                m.requirement_type,
                m.raw_text,
                m.structured_value

            FROM job_requirement_mentions
                AS m

            JOIN source_search_results
                AS ssres

                ON
                    m.job_id =
                    ssres.job_id

            JOIN source_search_runs
                AS ssr

                ON
                    ssres.source_search_run_id =
                    ssr.source_search_run_id

            WHERE
                m.extractor_version =
                    :extractor_version

                AND
                ssr.search_request_id =
                    :search_request_id

            ORDER BY
                m.requirement_mention_id;
        """

        parameters = {
            "extractor_version":
                REQUIREMENT_VERSION,

            "search_request_id":
                search_request_id,
        }


    with engine.connect() as connection:

        mentions = (
            connection.execute(
                text(query),
                parameters,
            )
            .mappings()
            .all()
        )


    print(
        f"Processing "
        f"{len(mentions)} "
        f"requirement mentions..."
    )


    created_links = 0


    for mention in mentions:

        candidates = (
            extract_atomic_concepts(
                mention[
                    "raw_text"
                ],

                mention[
                    "requirement_type"
                ],
                structured_value=(
                    mention.get(
                        "structured_value"
                    )
                    or {}
                ),
            )
        )


        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    DELETE FROM
                        job_requirement_concepts

                    WHERE
                        requirement_mention_id =
                            :requirement_mention_id

                        AND
                        extractor_version =
                            :extractor_version;
                    """
                ),
                {
                    "requirement_mention_id":
                        mention[
                            "requirement_mention_id"
                        ],

                    "extractor_version":
                        CONCEPT_EXTRACTOR_VERSION,
                },
            )


            for candidate in candidates:

                concept_id = (
                    connection.execute(
                        text(
                            """
                            INSERT INTO
                                requirement_concepts (
                                    concept_type,
                                    canonical_name,
                                    normalized_key
                                )

                            VALUES (
                                :concept_type,
                                :canonical_name,
                                :normalized_key
                            )

                            ON CONFLICT (
                                concept_type,
                                normalized_key
                            )

                            DO UPDATE SET
                                canonical_name =
                                    EXCLUDED.canonical_name

                            RETURNING
                                concept_id;
                            """
                        ),
                        {
                            "concept_type":
                                candidate.get(
                                    "concept_type",
                                    mention[
                                        "requirement_type"
                                    ],
                                ),

                            "canonical_name":
                                candidate[
                                    "raw_text"
                                ],

                            "normalized_key":
                                candidate[
                                    "normalized_key"
                                ],
                        },
                    )
                    .scalar_one()
                )


                connection.execute(
                    text(
                        """
                        INSERT INTO
                            requirement_concept_aliases (
                                concept_id,
                                alias_text,
                                normalized_alias,
                                alias_source
                            )

                        VALUES (
                            :concept_id,
                            :alias_text,
                            :normalized_alias,
                            'observed'
                        )

                        ON CONFLICT (
                            concept_id,
                            normalized_alias
                        )

                        DO NOTHING;
                        """
                    ),
                    {
                        "concept_id":
                            concept_id,

                        "alias_text":
                            candidate[
                                "raw_text"
                            ],

                        "normalized_alias":
                            candidate[
                                "normalized_key"
                            ],
                    },
                )


                connection.execute(
                    text(
                        """
                        INSERT INTO
                            job_requirement_concepts (
                                requirement_mention_id,
                                concept_id,
                                raw_concept_text,
                                extraction_method,
                                confidence,
                                extractor_version,
                                group_operator,
                                group_is_open
                            )

                        VALUES (
                            :requirement_mention_id,
                            :concept_id,
                            :raw_concept_text,
                            :extraction_method,
                            :confidence,
                            :extractor_version,
                            :group_operator,
                            :group_is_open
                        )

                        ON CONFLICT (
                            requirement_mention_id,
                            concept_id,
                            extractor_version
                        )

                        DO UPDATE SET
                            raw_concept_text =
                                EXCLUDED
                                .raw_concept_text,

                            extraction_method =
                                EXCLUDED
                                .extraction_method,

                            confidence =
                                EXCLUDED.confidence,

                            group_operator =
                                EXCLUDED
                                .group_operator,

                            group_is_open =
                                EXCLUDED
                                .group_is_open;
                        """
                    ),
                    {
                        "requirement_mention_id":
                            mention[
                                "requirement_mention_id"
                            ],

                        "concept_id":
                            concept_id,

                        "raw_concept_text":
                            candidate[
                                "raw_text"
                            ],

                        "extraction_method":
                            candidate.get(
                                "extraction_method",
                                "rule_based_atomic",
                            ),

                        "confidence":
                            candidate.get(
                                "confidence"
                            ),

                        "extractor_version":
                            CONCEPT_EXTRACTOR_VERSION,

                        "group_operator":
                            candidate[
                                "group_operator"
                            ],

                        "group_is_open":
                            candidate[
                                "group_is_open"
                            ],
                    },
                )


                created_links += 1


    print(
        f"Created "
        f"{created_links} "
        f"requirement-concept links."
    )


    return {
        "mentions_processed":
            len(mentions),

        "concept_links":
            created_links,

        "extractor_version":
            CONCEPT_EXTRACTOR_VERSION,
    }


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Build logical atomic "
            "CareerCompass requirement "
            "concepts."
        )
    )


    parser.add_argument(
        "--search-request-id",
        type=int,
        required=False,
    )


    args = parser.parse_args()


    build_requirement_concepts(
        search_request_id=
            args.search_request_id
    )