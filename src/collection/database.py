import json
import os

from sqlalchemy import (
    create_engine,
    text,
)

from sqlalchemy.engine import URL

def create_database_engine(
    database_url=None,
):
    database_url = (
        database_url
        or os.getenv("DATABASE_URL")
    )

    if database_url:
        return create_engine(
            database_url,
            pool_pre_ping=True,
        )

    database_url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )

def create_search_request(
    connection,
    query,
    location,
    country_code,
):

    return connection.execute(
        text(
            """
            INSERT INTO search_requests (
                query_text,
                location_text,
                country_code
            )
            VALUES (
                :query,
                :location,
                :country_code
            )
            RETURNING search_request_id;
            """
        ),
        {
            "query": query,
            "location": location,
            "country_code":
                country_code,
        },
    ).scalar_one()


def start_source_run(
    connection,
    search_request_id,
    source,
    raw_response_dir,
):

    return connection.execute(
        text(
            """
            INSERT INTO source_search_runs (
                search_request_id,
                source,
                raw_response_dir
            )
            VALUES (
                :search_request_id,
                :source,
                :raw_response_dir
            )
            RETURNING source_search_run_id;
            """
        ),
        {
            "search_request_id":
                search_request_id,

            "source":
                source,

            "raw_response_dir":
                raw_response_dir,
        },
    ).scalar_one()


def finish_source_run(
    connection,
    source_search_run_id,
    status,
    reported_count,
    pages_fetched,
    jobs_returned,
    error_message=None,
):

    connection.execute(
        text(
            """
            UPDATE source_search_runs
            SET
                completed_at = NOW(),
                status = :status,
                reported_count =
                    :reported_count,
                pages_fetched =
                    :pages_fetched,
                jobs_returned =
                    :jobs_returned,
                error_message =
                    :error_message
            WHERE source_search_run_id =
                :source_search_run_id;
            """
        ),
        {
            "status":
                status,

            "reported_count":
                reported_count,

            "pages_fetched":
                pages_fetched,

            "jobs_returned":
                jobs_returned,

            "error_message":
                error_message,

            "source_search_run_id":
                source_search_run_id,
        },
    )


def upsert_job(
    connection,
    job,
):

    company_name = (
        job.company_name
        or (
            "Unknown Company "
            f"[{job.source}:"
            f"{job.source_job_id}]"
        )
    )

    company_id = connection.execute(
        text(
            """
            INSERT INTO companies (
                canonical_name
            )
            VALUES (
                :company_name
            )

            ON CONFLICT (
                canonical_name
            )

            DO UPDATE SET
                canonical_name =
                    EXCLUDED.canonical_name

            RETURNING company_id;
            """
        ),
        {
            "company_name":
                company_name
        },
    ).scalar_one()


    return connection.execute(
        text(
            """
            INSERT INTO jobs (
                company_id,
                raw_company_name,

                source,
                source_job_id,

                job_url,

                raw_title,
                canonical_role,

                location_raw,
                location_country,

                employment_type,
                salary_text,

                description,
                date_posted,

                last_seen_at,
                is_active,

                source_metadata
            )

            VALUES (
                :company_id,
                :company_name,

                :source,
                :source_job_id,

                :job_url,

                :title,
                NULL,

                :location_raw,
                :location_country,

                :employment_type,
                :salary_text,

                :description,
                :date_posted,

                NOW(),
                TRUE,

                CAST(
                    :source_metadata
                    AS JSONB
                )
            )

            ON CONFLICT (
                source,
                source_job_id
            )

            WHERE source_job_id
                IS NOT NULL

            DO UPDATE SET

                company_id =
                    EXCLUDED.company_id,

                raw_company_name =
                    EXCLUDED.raw_company_name,

                job_url =
                    EXCLUDED.job_url,

                raw_title =
                    EXCLUDED.raw_title,

                location_raw =
                    EXCLUDED.location_raw,

                location_country =
                    EXCLUDED.location_country,

                employment_type =
                    EXCLUDED.employment_type,

                salary_text =
                    EXCLUDED.salary_text,

                description =
                    EXCLUDED.description,

                date_posted =
                    EXCLUDED.date_posted,

                last_seen_at =
                    NOW(),

                is_active =
                    TRUE,

                source_metadata =
                    EXCLUDED.source_metadata

            RETURNING job_id;
            """
        ),
        {
            "company_id":
                company_id,

            "company_name":
                company_name,

            "source":
                job.source,

            "source_job_id":
                job.source_job_id,

            "job_url":
                job.job_url,

            "title":
                job.title,

            "location_raw":
                job.location_raw,

            "location_country":
                job.location_country,

            "employment_type":
                job.employment_type,

            "salary_text":
                job.salary_text,

            "description":
                job.description,

            "date_posted":
                job.date_posted,

            "source_metadata":
                json.dumps(
                    job.metadata
                ),
        },
    ).scalar_one()


def link_job_to_source_run(
    connection,
    source_search_run_id,
    job_id,
    page_number,
    result_rank,
):

    connection.execute(
        text(
            """
            INSERT INTO source_search_results (
                source_search_run_id,
                job_id,
                page_number,
                result_rank
            )

            VALUES (
                :source_search_run_id,
                :job_id,
                :page_number,
                :result_rank
            )

            ON CONFLICT (
                source_search_run_id,
                job_id
            )

            DO NOTHING;
            """
        ),
        {
            "source_search_run_id":
                source_search_run_id,

            "job_id":
                job_id,

            "page_number":
                page_number,

            "result_rank":
                result_rank,
        },
    )