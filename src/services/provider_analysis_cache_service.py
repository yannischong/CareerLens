import json

from sqlalchemy import text


JOB_ANALYSIS_VERSION = (
    "provider_job_ai_v6_original_source"
)

PROFILE_ANALYSIS_VERSION = (
    "provider_resume_ai_v6_original_source"
)


def _table_exists(
    connection,
    table_name,
):
    return bool(
        connection.execute(
            text(
                """
                SELECT
                    to_regclass(
                        :table_name
                    )
                    IS NOT NULL;
                """
            ),
            {
                "table_name":
                    f"public.{table_name}",
            },
        ).scalar_one()
    )


def cache_tables_available(
    connection,
):
    return (
        _table_exists(
            connection,
            "provider_job_analysis_cache",
        )
        and
        _table_exists(
            connection,
            "provider_profile_analysis_cache",
        )
    )


def get_cached_job_analysis(
    connection,
    job_id,
    job_content_hash,
):
    if not _table_exists(
        connection,
        "provider_job_analysis_cache",
    ):
        return None

    row = (
        connection.execute(
            text(
                """
                SELECT
                    analysis_method,
                    requirements,
                    skills

                FROM
                    provider_job_analysis_cache

                WHERE
                    job_id =
                        :job_id

                    AND
                    job_content_hash =
                        :job_content_hash

                    AND
                    analysis_version =
                        :analysis_version

                LIMIT 1;
                """
            ),
            {
                "job_id":
                    job_id,

                "job_content_hash":
                    job_content_hash,

                "analysis_version":
                    JOB_ANALYSIS_VERSION,
            },
        )
        .mappings()
        .one_or_none()
    )

    return (
        dict(row)
        if row is not None
        else None
    )


def store_job_analysis(
    connection,
    job_id,
    job_content_hash,
    analysis_method,
    requirements,
    skills,
):
    if not _table_exists(
        connection,
        "provider_job_analysis_cache",
    ):
        return False

    connection.execute(
        text(
            """
                INSERT INTO
                    provider_job_analysis_cache (
                        job_id,
                        job_content_hash,
                        analysis_version,
                        analysis_method,
                        requirements,
                        skills
                    )

                VALUES (
                    :job_id,
                    :job_content_hash,
                    :analysis_version,
                    :analysis_method,

                    CAST(
                        :requirements
                        AS JSONB
                    ),

                    CAST(
                        :skills
                        AS JSONB
                    )
                )

                ON CONFLICT (
                    job_id,
                    job_content_hash,
                    analysis_version
                )

                DO UPDATE SET
                    analysis_method =
                        EXCLUDED.analysis_method,

                    requirements =
                        EXCLUDED.requirements,

                    skills =
                        EXCLUDED.skills,

                    updated_at =
                        NOW();
            """
        ),
        {
            "job_id":
                job_id,

            "job_content_hash":
                job_content_hash,

            "analysis_version":
                JOB_ANALYSIS_VERSION,

            "analysis_method":
                analysis_method,

            "requirements":
                json.dumps(
                    requirements
                ),

            "skills":
                json.dumps(
                    skills
                ),
        },
    )

    return True


def get_cached_profile_analysis(
    connection,
    profile_id,
    job_id,
    resume_id,
    job_content_hash,
):
    if not _table_exists(
        connection,
        "provider_profile_analysis_cache",
    ):
        return None

    row = (
        connection.execute(
            text(
                """
                SELECT
                    analysis_payload,
                    resume_match_percentage

                FROM
                    provider_profile_analysis_cache

                WHERE
                    profile_id =
                        :profile_id

                    AND
                    job_id =
                        :job_id

                    AND
                    resume_id =
                        :resume_id

                    AND
                    job_content_hash =
                        :job_content_hash

                    AND
                    job_analysis_version =
                        :job_analysis_version

                    AND
                    fit_version =
                        :fit_version

                LIMIT 1;
                """
            ),
            {
                "profile_id":
                    profile_id,

                "job_id":
                    job_id,

                "resume_id":
                    resume_id,

                "job_content_hash":
                    job_content_hash,

                "job_analysis_version":
                    JOB_ANALYSIS_VERSION,

                "fit_version":
                    PROFILE_ANALYSIS_VERSION,
            },
        )
        .mappings()
        .one_or_none()
    )

    return (
        dict(row)
        if row is not None
        else None
    )


def store_profile_analysis(
    connection,
    profile_id,
    job_id,
    resume_id,
    job_content_hash,
    analysis_payload,
    resume_match_percentage,
):
    if not _table_exists(
        connection,
        "provider_profile_analysis_cache",
    ):
        return False

    connection.execute(
        text(
            """
                INSERT INTO
                    provider_profile_analysis_cache (
                        profile_id,
                        job_id,
                        resume_id,
                        job_content_hash,
                        job_analysis_version,
                        fit_version,
                        analysis_payload,
                        resume_match_percentage
                    )

                VALUES (
                    :profile_id,
                    :job_id,
                    :resume_id,
                    :job_content_hash,
                    :job_analysis_version,
                    :fit_version,

                    CAST(
                        :analysis_payload
                        AS JSONB
                    ),

                    :resume_match_percentage
                )

                ON CONFLICT (
                    profile_id,
                    job_id,
                    resume_id,
                    job_content_hash,
                    job_analysis_version,
                    fit_version
                )

                DO UPDATE SET
                    analysis_payload =
                        EXCLUDED.analysis_payload,

                    resume_match_percentage =
                        EXCLUDED.resume_match_percentage,

                    updated_at =
                        NOW();
            """
        ),
        {
            "profile_id":
                profile_id,

            "job_id":
                job_id,

            "resume_id":
                resume_id,

            "job_content_hash":
                job_content_hash,

            "job_analysis_version":
                JOB_ANALYSIS_VERSION,

            "fit_version":
                PROFILE_ANALYSIS_VERSION,

            "analysis_payload":
                json.dumps(
                    analysis_payload
                ),

            "resume_match_percentage":
                resume_match_percentage,
        },
    )

    return True


def get_cached_profile_analyses_for_search(
    connection,
    profile_id,
    resume_id,
    search_request_id,
):
    if (
        resume_id is None
        or not _table_exists(
            connection,
            "provider_profile_analysis_cache",
        )
    ):
        return {}

    rows = (
        connection.execute(
            text(
                """
                SELECT
                    cache.job_id,
                    cache.job_content_hash,
                    cache.analysis_payload,
                    cache.resume_match_percentage

                FROM
                    provider_profile_analysis_cache
                    AS cache

                WHERE
                    cache.profile_id =
                        :profile_id

                    AND
                    cache.resume_id =
                        :resume_id

                    AND
                    cache.job_analysis_version =
                        :job_analysis_version

                    AND
                    cache.fit_version =
                        :fit_version

                    AND EXISTS (
                        SELECT 1

                        FROM
                            source_search_results
                            AS ssres

                        JOIN
                            source_search_runs
                            AS ssr

                            ON
                                ssr.source_search_run_id =
                                    ssres.source_search_run_id

                        WHERE
                            ssres.job_id =
                                cache.job_id

                            AND
                            ssr.search_request_id =
                                :search_request_id
                    );
                """
            ),
            {
                "profile_id":
                    profile_id,

                "resume_id":
                    resume_id,

                "search_request_id":
                    search_request_id,

                "job_analysis_version":
                    JOB_ANALYSIS_VERSION,

                "fit_version":
                    PROFILE_ANALYSIS_VERSION,
            },
        )
        .mappings()
        .all()
    )

    return {
        (
            int(
                row[
                    "job_id"
                ]
            ),
            row[
                "job_content_hash"
            ],
        ):
            dict(row)

        for row in rows
    }
