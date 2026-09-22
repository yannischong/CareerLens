import argparse

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)
from src.ranking.lexical import (
    calculate_tfidf_scores,
)
from src.ranking.semantic import (
    MODEL_NAME,
    calculate_semantic_scores,
)


SCORING_VERSION = "relevance_v1"


load_dotenv()


def rank_search(
    search_request_id,
    database_url=None,
):
    engine = create_database_engine(
        database_url
    )

    with engine.connect() as connection:
        search_request = (
            connection.execute(
                text(
                    """
                    SELECT
                        search_request_id,
                        query_text

                    FROM search_requests

                    WHERE
                        search_request_id =
                            :search_request_id;
                    """
                ),
                {
                    "search_request_id":
                        search_request_id,
                },
            )
            .mappings()
            .first()
        )

    if search_request is None:
        raise ValueError(
            "Search request not found."
        )

    query = search_request[
        "query_text"
    ]

    with engine.connect() as connection:
        jobs = (
            connection.execute(
                text(
                    """
                    SELECT DISTINCT
                        j.job_id,
                        j.raw_title,
                        j.normalized_title,
                        j.description,
                        j.normalized_description,
                        j.raw_company_name,
                        j.source

                    FROM jobs AS j

                    JOIN source_search_results
                        AS ssres

                        ON j.job_id =
                           ssres.job_id

                    JOIN source_search_runs
                        AS ssr

                        ON
                            ssres.source_search_run_id =
                            ssr.source_search_run_id

                    WHERE
                        ssr.search_request_id =
                            :search_request_id

                    ORDER BY j.job_id;
                    """
                ),
                {
                    "search_request_id":
                        search_request_id,
                },
            )
            .mappings()
            .all()
        )

    if not jobs:
        raise ValueError(
            "No jobs found for this "
            "search request."
        )

    print(
        f"Search query: {query}"
    )

    print(
        f"Jobs to rank: {len(jobs)}"
    )

    tfidf_results = (
        calculate_tfidf_scores(
            query,
            jobs,
        )
    )

    semantic_results = (
        calculate_semantic_scores(
            query,
            jobs,
        )
    )

    def store_scores(
        method,
        model_name,
        results,
    ):
        ranked_results = sorted(
            results,
            key=lambda result:
                result["combined_score"],
            reverse=True,
        )

        with engine.begin() as connection:
            for rank, result in enumerate(
                ranked_results,
                start=1,
            ):
                connection.execute(
                    text(
                        """
                        INSERT INTO
                            job_relevance_scores (
                                search_request_id,
                                job_id,
                                scoring_method,
                                model_name,
                                title_score,
                                description_score,
                                combined_score,
                                rank_position,
                                scoring_version
                            )

                        VALUES (
                            :search_request_id,
                            :job_id,
                            :scoring_method,
                            :model_name,
                            :title_score,
                            :description_score,
                            :combined_score,
                            :rank_position,
                            :scoring_version
                        )

                        ON CONFLICT (
                            search_request_id,
                            job_id,
                            scoring_method,
                            model_name
                        )

                        DO UPDATE SET
                            title_score =
                                EXCLUDED.title_score,

                            description_score =
                                EXCLUDED.description_score,

                            combined_score =
                                EXCLUDED.combined_score,

                            rank_position =
                                EXCLUDED.rank_position,

                            scoring_version =
                                EXCLUDED.scoring_version,

                            scored_at =
                                NOW();
                        """
                    ),
                    {
                        "search_request_id":
                            search_request_id,

                        "job_id":
                            result["job_id"],

                        "scoring_method":
                            method,

                        "model_name":
                            model_name,

                        "title_score":
                            result["title_score"],

                        "description_score":
                            result[
                                "description_score"
                            ],

                        "combined_score":
                            result[
                                "combined_score"
                            ],

                        "rank_position":
                            rank,

                        "scoring_version":
                            SCORING_VERSION,
                    },
                )

    store_scores(
        "tfidf",
        "tfidf_1_2gram",
        tfidf_results,
    )

    store_scores(
        "semantic",
        MODEL_NAME,
        semantic_results,
    )

    print(
        "Stored TF-IDF and "
        "semantic rankings."
    )

    return {
        "search_request_id":
            search_request_id,

        "jobs_ranked":
            len(jobs),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Rank CareerCompass search results "
            "against the user's "
            "occupation query."
        )
    )

    parser.add_argument(
        "--search-request-id",
        type=int,
        required=True,
    )

    args = parser.parse_args()

    rank_search(
        search_request_id=
            args.search_request_id
    )