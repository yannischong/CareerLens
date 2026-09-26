import json
import os
import re

from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
    create_search_request,
    finish_source_run,
    link_job_to_source_run,
    start_source_run,
    upsert_job,
)

from src.collection.providers.jooble import (
    search_jooble,
)

from src.collection.providers.serpapi import (
    search_serpapi,
)

from src.collection.providers.web_discovery import (
    search_web_discovery,
)


load_dotenv()


VALID_PROVIDERS = {
    "serpapi",
    "jooble",
}


def run_job_search(
    query,
    location="Singapore",
    country="sg",
    providers=None,
    pages=1,
    database_url=None,
):
    if providers is None:
        providers = [
            "serpapi",
            "jooble",
        ]

    if not query.strip():
        raise ValueError(
            "Search query cannot be empty."
        )

    if pages < 1:
        raise ValueError(
            "Pages must be at least 1."
        )

    invalid_providers = (
        set(providers)
        - VALID_PROVIDERS
    )

    if invalid_providers:
        raise ValueError(
            "Invalid providers: "
            + ", ".join(
                sorted(
                    invalid_providers
                )
            )
        )


    engine = create_database_engine(database_url)


    with engine.begin() as connection:

        search_request_id = (
            create_search_request(
                connection,
                query.strip(),
                location.strip(),
                country.lower(),
            )
        )


    safe_query = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        query.strip(),
    ).strip("_")


    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )


    raw_root = (
        Path("data/raw/jobs")
        / (
            f"{timestamp}_"
            f"{search_request_id}_"
            f"{safe_query}"
        )
    )

    raw_root.mkdir(
        parents=True,
        exist_ok=True,
    )


    provider_results = []

    effective_providers = list(providers)

    web_discovery_enabled = (
        os.getenv(
            "WEB_DISCOVERY_ENABLED",
            "true",
        ).strip().lower()
        not in {"0", "false", "no", "off"}
    )

    if (
        web_discovery_enabled
        and "serpapi" in providers
        and "web_discovery" not in effective_providers
    ):
        effective_providers.append(
            "web_discovery"
        )


    for provider_name in effective_providers:

        provider_directory = (
            raw_root
            / provider_name
        )

        provider_directory.mkdir(
            parents=True,
            exist_ok=True,
        )


        with engine.begin() as connection:

            source_search_run_id = (
                start_source_run(
                    connection,
                    search_request_id,
                    provider_name,
                    str(
                        provider_directory
                    ),
                )
            )


        if provider_name == "serpapi":

            api_key = os.getenv(
                "SERPAPI_API_KEY"
            )

            if not api_key:

                with engine.begin() as connection:

                    finish_source_run(
                        connection,
                        source_search_run_id,
                        "skipped",
                        None,
                        0,
                        0,
                        "SERPAPI_API_KEY missing",
                    )

                provider_results.append(
                    {
                        "provider":
                            provider_name,

                        "status":
                            "skipped",

                        "pages_fetched":
                            0,

                        "jobs_returned":
                            0,

                        "error":
                            (
                                "SERPAPI_API_KEY "
                                "missing"
                            ),
                    }
                )

                continue


            provider_pages = (
                search_serpapi(
                    query,
                    location,
                    country,
                    api_key,
                    pages,
                )
            )


        elif provider_name == "web_discovery":

            api_key = os.getenv(
                "SERPAPI_API_KEY"
            )

            if not api_key:

                with engine.begin() as connection:

                    finish_source_run(
                        connection,
                        source_search_run_id,
                        "skipped",
                        None,
                        0,
                        0,
                        "SERPAPI_API_KEY missing",
                    )

                provider_results.append(
                    {
                        "provider":
                            provider_name,

                        "status":
                            "skipped",

                        "pages_fetched":
                            0,

                        "jobs_returned":
                            0,

                        "error":
                            (
                                "SERPAPI_API_KEY "
                                "missing"
                            ),
                    }
                )

                continue

            provider_pages = (
                search_web_discovery(
                    query,
                    location,
                    country,
                    api_key,
                )
            )


        elif provider_name == "jooble":

            api_key = os.getenv(
                "JOOBLE_API_KEY"
            )

            base_url = os.getenv(
                "JOOBLE_BASE_URL",
                "https://sg.jooble.org",
            )


            if not api_key:

                with engine.begin() as connection:

                    finish_source_run(
                        connection,
                        source_search_run_id,
                        "skipped",
                        None,
                        0,
                        0,
                        "JOOBLE_API_KEY missing",
                    )

                provider_results.append(
                    {
                        "provider":
                            provider_name,

                        "status":
                            "skipped",

                        "pages_fetched":
                            0,

                        "jobs_returned":
                            0,

                        "error":
                            (
                                "JOOBLE_API_KEY "
                                "missing"
                            ),
                    }
                )

                continue


            provider_pages = (
                search_jooble(
                    query,
                    location,
                    api_key,
                    base_url,
                    pages,
                )
            )


        pages_fetched = 0
        reported_count = None

        job_ids = set()

        result_rank = 0


        try:

            for provider_page in (
                provider_pages
            ):

                pages_fetched += 1


                if (
                    provider_page
                    .reported_count
                    is not None
                ):
                    reported_count = (
                        provider_page
                        .reported_count
                    )


                raw_file = (
                    provider_directory
                    / (
                        "page_"
                        f"{provider_page.page_number}"
                        ".json"
                    )
                )


                with open(
                    raw_file,
                    "w",
                    encoding="utf-8",
                ) as file:

                    json.dump(
                        provider_page.payload,
                        file,
                        ensure_ascii=False,
                        indent=2,
                    )


                with engine.begin() as connection:

                    for job in (
                        provider_page.jobs
                    ):

                        result_rank += 1

                        existing_job_id = None

                        if provider_name == "web_discovery":
                            existing_job_id = (
                                connection.execute(
                                    text(
                                        """
                                        SELECT j.job_id
                                        FROM jobs j
                                        JOIN source_search_results ssres
                                            ON ssres.job_id = j.job_id
                                        JOIN source_search_runs ssr
                                            ON ssr.source_search_run_id =
                                               ssres.source_search_run_id
                                        WHERE
                                            ssr.search_request_id =
                                                :search_request_id
                                            AND LOWER(
                                                REGEXP_REPLACE(
                                                    SPLIT_PART(j.job_url, '?', 1),
                                                    '/+$',
                                                    ''
                                                )
                                            ) = LOWER(
                                                REGEXP_REPLACE(
                                                    SPLIT_PART(:job_url, '?', 1),
                                                    '/+$',
                                                    ''
                                                )
                                            )
                                        LIMIT 1;
                                        """
                                    ),
                                    {
                                        "search_request_id":
                                            search_request_id,
                                        "job_url":
                                            job.job_url,
                                    },
                                ).scalar_one_or_none()
                            )

                        job_id = (
                            existing_job_id
                            or upsert_job(
                                connection,
                                job,
                            )
                        )


                        link_job_to_source_run(
                            connection,
                            source_search_run_id,
                            job_id,
                            provider_page.page_number,
                            result_rank,
                        )


                        job_ids.add(
                            job_id
                        )


            with engine.begin() as connection:

                finish_source_run(
                    connection,
                    source_search_run_id,
                    "completed",
                    reported_count,
                    pages_fetched,
                    len(job_ids),
                )


            provider_results.append(
                {
                    "provider":
                        provider_name,

                    "status":
                        "completed",

                    "reported_count":
                        reported_count,

                    "pages_fetched":
                        pages_fetched,

                    "jobs_returned":
                        len(job_ids),

                    "error":
                        None,
                }
            )


        except Exception as error:

            with engine.begin() as connection:

                finish_source_run(
                    connection,
                    source_search_run_id,
                    "failed",
                    reported_count,
                    pages_fetched,
                    len(job_ids),
                    str(error)[:2000],
                )


            provider_results.append(
                {
                    "provider":
                        provider_name,

                    "status":
                        "failed",

                    "reported_count":
                        reported_count,

                    "pages_fetched":
                        pages_fetched,

                    "jobs_returned":
                        len(job_ids),

                    "error":
                        str(error),
                }
            )


    return {
        "search_request_id":
            search_request_id,

        "query":
            query,

        "location":
            location,

        "country":
            country,

        "providers":
            provider_results,

        "raw_response_directory":
            str(raw_root),
    }