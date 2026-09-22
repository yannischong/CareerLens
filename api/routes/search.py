import os

from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import text

from api.profile import (
    CurrentProfile,
    get_current_profile,
)
from api.schemas.search import (
    JobSearchRequest,
)
from src.cleaning.normalize_jobs import (
    normalize_jobs,
)
from src.collection.database import (
    create_database_engine,
)
from src.eligibility.assess_eligibility import (
    assess_eligibility,
)
from src.eligibility.extract_job_eligibility import (
    extract_job_eligibility,
)
from src.eligibility.extract_profile_facts import (
    extract_profile_facts,
)
from src.extraction.extract_requirements import (
    extract_job_requirements,
)
from src.matching.assess_fit import (
    assess_profile_fit,
)
from src.ranking.rank_search import (
    rank_search,
)
from src.services.job_search_service import (
    run_job_search,
)
from src.services.search_quota_service import (
    get_search_quota,
    reserve_search_slot,
)
from src.taxonomy.build_requirement_concepts import (
    build_requirement_concepts,
)


load_dotenv()


router = APIRouter(
    prefix="/api/search",
    tags=["Search"],
)


DATABASE_URL = os.getenv(
    "SUPABASE_DATABASE_URL"
)


engine = create_database_engine(
    DATABASE_URL
)


PROFILE_FIT_VERSION = (
    "profile_fit_v2"
)

REQUIREMENT_VERSION = (
    "requirements_v2"
)

CONCEPT_VERSION = (
    "atomic_concepts_v2"
)


def profile_has_resume(
    profile_id,
):
    with engine.connect() as connection:

        return connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1

                    FROM resume_documents

                    WHERE
                        profile_id =
                            :profile_id
                );
                """
            ),
            {
                "profile_id":
                    profile_id,
            },
        ).scalar_one()


def refresh_search_assessments(
    profile_id,
    search_request_id,
):
    eligibility_extraction = (
        extract_job_eligibility(
            database_url=
                DATABASE_URL,

            search_request_id=
                search_request_id,
        )
    )


    if not profile_has_resume(
        profile_id
    ):
        return {
            "profile_available":
                False,

            "job_eligibility":
                eligibility_extraction,

            "profile_facts":
                None,

            "profile_fit":
                None,

            "eligibility":
                None,
        }


    profile_facts = (
        extract_profile_facts(
            profile_id=
                profile_id,

            database_url=
                DATABASE_URL,
        )
    )


    fit_result = (
        assess_profile_fit(
            profile_id=
                profile_id,

            search_request_id=
                search_request_id,

            database_url=
                DATABASE_URL,
        )
    )


    eligibility_result = (
        assess_eligibility(
            profile_id=
                profile_id,

            search_request_id=
                search_request_id,

            database_url=
                DATABASE_URL,
        )
    )


    return {
        "profile_available":
            True,

        "job_eligibility":
            eligibility_extraction,

        "profile_facts":
            profile_facts,

        "profile_fit":
            fit_result,

        "eligibility":
            eligibility_result,
    }


def fetch_search_results(
    connection,
    search_request_id,
    profile_id,
):
    rows = connection.execute(
        text(
            """
            WITH search_jobs AS (
                SELECT
                    r.job_id,

                    MIN(
                        r.result_rank
                    ) AS provider_rank

                FROM source_search_runs sr

                JOIN source_search_results r
                    ON
                        r.source_search_run_id =
                        sr.source_search_run_id

                WHERE
                    sr.search_request_id =
                        :search_request_id

                GROUP BY
                    r.job_id
            )

            SELECT
                j.job_id,
                j.raw_title,
                j.raw_company_name,
                j.location_raw,
                j.employment_type,
                j.salary_text,
                j.description,
                j.job_url,
                j.source,
                j.date_posted,
                j.derived_posted_date,

                rel.combined_score
                    AS search_relevance,

                rel.rank_position
                    AS relevance_rank,

                sj.provider_rank,

                EXISTS (
                    SELECT 1

                    FROM job_quality_flags dq

                    WHERE
                        dq.job_id =
                            j.job_id

                        AND
                        dq.generated_by =
                            'normalize_v1'

                        AND
                        dq.flag_code =
                            'insufficient_description'
                ) AS insufficient_description,

                COALESCE(
                    (
                        SELECT
                            jsonb_agg(
                                jsonb_build_object(
                                    'flag_code',
                                        q.flag_code,

                                    'details',
                                        q.details
                                )

                                ORDER BY
                                    q.flag_code
                            )

                        FROM
                            job_quality_flags q

                        WHERE
                            q.job_id =
                                j.job_id

                            AND
                            q.generated_by =
                                'normalize_v1'
                    ),

                    '[]'::jsonb
                ) AS quality_flags,

                COALESCE(
                    (
                        SELECT
                            jsonb_agg(
                                jsonb_build_object(
                                    'id',
                                        req.requirement_mention_id,

                                    'type',
                                        req.requirement_type,

                                    'level',
                                        req.requirement_level,

                                    'text',
                                        req.raw_text,

                                    'structured_value',
                                        req.structured_value
                                )

                                ORDER BY
                                    CASE
                                        WHEN
                                            req.requirement_level =
                                            'required'
                                        THEN 1

                                        WHEN
                                            req.requirement_level =
                                            'preferred'
                                        THEN 2

                                        ELSE 3
                                    END,

                                    req.requirement_mention_id
                            )

                        FROM (
                            SELECT DISTINCT ON (
                                m.requirement_type,
                                m.requirement_level,
                                m.normalized_text
                            )
                                m.requirement_mention_id,
                                m.requirement_type,
                                m.requirement_level,
                                m.raw_text,
                                m.normalized_text,
                                m.structured_value

                            FROM
                                job_requirement_mentions m

                            WHERE
                                m.job_id =
                                    j.job_id

                                AND
                                m.extractor_version =
                                    :requirement_version

                            ORDER BY
                                m.requirement_type,
                                m.requirement_level,
                                m.normalized_text,
                                m.requirement_mention_id
                        ) req
                    ),

                    '[]'::jsonb
                ) AS requirements,


                CASE
                    WHEN EXISTS (
                        SELECT 1

                        FROM job_quality_flags dq

                        WHERE
                            dq.job_id =
                                j.job_id

                            AND
                            dq.generated_by =
                                'normalize_v1'

                            AND
                            dq.flag_code =
                                'insufficient_description'
                    )

                    THEN
                        jsonb_build_object(
                            'status',
                                'insufficient_job_data',

                            'model_version',
                                :profile_fit_version,

                            'reason',
                                (
                                    'The available job description '
                                    'is only a short snippet or does '
                                    'not contain enough information '
                                    'for reliable profile matching.'
                                )
                        )


                    WHEN
                        fit.job_id IS NULL

                    THEN NULL


                    ELSE
                        jsonb_build_object(
                            'status',
                                'assessed',

                            'model_version',
                                :profile_fit_version,


                            /*
                             * Atomic concept metrics.
                             *
                             * These remain available for
                             * diagnostics and backwards
                             * compatibility.
                             */

                            'total_concepts',
                                fit.total_concepts,

                            'required_concepts',
                                fit.required_concepts,

                            'preferred_concepts',
                                fit.preferred_concepts,

                            'unknown_level_concepts',
                                fit.unknown_level_concepts,

                            'evidenced',
                                fit.evidenced_concepts,

                            'claimed_only',
                                fit.claimed_only_concepts,

                            'candidate',
                                fit.candidate_concepts,

                            'gaps',
                                fit.gap_concepts,

                            'required_candidates',
                                fit.required_candidate_concepts,

                            'required_gaps',
                                fit.required_gap_concepts,


                            /*
                             * Logical requirement-group
                             * metrics.
                             *
                             * These are the primary v2
                             * Profile Fit measurements.
                             */

                            'total_groups',
                                fit.total_requirement_groups,

                            'required_groups',
                                fit.required_requirement_groups,

                            'preferred_groups',
                                fit.preferred_requirement_groups,

                            'unknown_groups',
                                fit.unknown_requirement_groups,

                            'group_evidenced',
                                fit.evidenced_requirement_groups,

                            'group_claimed_only',
                                fit.claimed_only_requirement_groups,

                            'group_candidate',
                                fit.candidate_requirement_groups,

                            'group_gaps',
                                fit.gap_requirement_groups,

                            'required_candidate_groups',
                                fit.required_candidate_groups,

                            'required_gap_groups',
                                fit.required_gap_groups,

                            'needs_review',
                                fit.unresolved_requirements,


                            /*
                             * Atomic concepts are retained
                             * for transparency.
                             */

                            'concepts',
                                COALESCE(
                                    (
                                        SELECT
                                            jsonb_agg(
                                                jsonb_build_object(
                                                    'concept_id',
                                                        cf.concept_id,

                                                    'name',
                                                        c.canonical_name,

                                                    'type',
                                                        cf.requirement_type,

                                                    'level',
                                                        cf.requirement_level,

                                                    'fit_status',
                                                        cf.fit_status,

                                                    'claim_status',
                                                        cf.claim_status,

                                                    'evidence_status',
                                                        cf.evidence_status
                                                )

                                                ORDER BY
                                                    CASE
                                                        WHEN
                                                            cf.requirement_level =
                                                            'required'
                                                        THEN 1

                                                        WHEN
                                                            cf.requirement_level =
                                                            'preferred'
                                                        THEN 2

                                                        ELSE 3
                                                    END,

                                                    c.canonical_name
                                            )

                                        FROM
                                            job_profile_concept_fit cf

                                        JOIN
                                            requirement_concepts c

                                            ON
                                                c.concept_id =
                                                cf.concept_id

                                        WHERE
                                            cf.profile_id =
                                                :profile_id

                                            AND
                                            cf.job_id =
                                                j.job_id

                                            AND
                                            cf.fit_version =
                                                :profile_fit_version
                                    ),

                                    '[]'::jsonb
                                ),


                            /*
                             * v2 logical groups.
                             */

                            'groups',
                                COALESCE(
                                    (
                                        SELECT
                                            jsonb_agg(
                                                jsonb_build_object(
                                                    'requirement_mention_id',
                                                        r.requirement_mention_id,

                                                    'type',
                                                        r.requirement_type,

                                                    'level',
                                                        r.requirement_level,

                                                    'text',
                                                        r.raw_text,

                                                    'operator',
                                                        gf.group_operator,

                                                    'is_open',
                                                        gf.group_is_open,

                                                    'status',
                                                        gf.assessment_status,

                                                    'explanation',
                                                        gf.explanation,

                                                    'matched_concept_id',
                                                        gf.matched_concept_id,

                                                    'matched_concept_name',
                                                        matched
                                                        .canonical_name,

                                                    'concepts',
                                                        COALESCE(
                                                            (
                                                                SELECT
                                                                    jsonb_agg(
                                                                        jsonb_build_object(
                                                                            'concept_id',
                                                                                member_concept
                                                                                .concept_id,

                                                                            'name',
                                                                                member_concept
                                                                                .canonical_name,

                                                                            'claim_status',
                                                                                member_fit
                                                                                .claim_status,

                                                                            'evidence_status',
                                                                                member_fit
                                                                                .evidence_status,

                                                                            'fit_status',
                                                                                member_fit
                                                                                .fit_status
                                                                        )

                                                                        ORDER BY
                                                                            member_concept
                                                                            .canonical_name
                                                                    )

                                                                FROM
                                                                    job_requirement_concepts
                                                                    member_link

                                                                JOIN
                                                                    requirement_concepts
                                                                    member_concept

                                                                    ON
                                                                        member_concept
                                                                        .concept_id =
                                                                        member_link
                                                                        .concept_id

                                                                LEFT JOIN
                                                                    job_profile_concept_fit
                                                                    member_fit

                                                                    ON
                                                                        member_fit
                                                                        .profile_id =
                                                                        :profile_id

                                                                        AND
                                                                        member_fit
                                                                        .job_id =
                                                                        j.job_id

                                                                        AND
                                                                        member_fit
                                                                        .concept_id =
                                                                        member_concept
                                                                        .concept_id

                                                                        AND
                                                                        member_fit
                                                                        .fit_version =
                                                                        :profile_fit_version

                                                                WHERE
                                                                    member_link
                                                                    .requirement_mention_id =
                                                                    r.requirement_mention_id

                                                                    AND
                                                                    member_link
                                                                    .extractor_version =
                                                                    :concept_version
                                                            ),

                                                            '[]'::jsonb
                                                        )
                                                )

                                                ORDER BY
                                                    CASE
                                                        WHEN
                                                            r.requirement_level =
                                                            'required'
                                                        THEN 1

                                                        WHEN
                                                            r.requirement_level =
                                                            'preferred'
                                                        THEN 2

                                                        ELSE 3
                                                    END,

                                                    r.requirement_mention_id
                                            )

                                        FROM
                                            job_profile_requirement_group_fit
                                            gf

                                        JOIN
                                            job_requirement_mentions r

                                            ON
                                                r.requirement_mention_id =
                                                gf.requirement_mention_id

                                        LEFT JOIN
                                            requirement_concepts matched

                                            ON
                                                matched.concept_id =
                                                gf.matched_concept_id

                                        WHERE
                                            gf.profile_id =
                                                :profile_id

                                            AND
                                            gf.fit_version =
                                                :profile_fit_version

                                            AND
                                            r.job_id =
                                                j.job_id

                                            AND
                                            r.extractor_version =
                                                :requirement_version
                                    ),

                                    '[]'::jsonb
                                ),


                            /*
                             * Requirements that could not
                             * yet be represented as a
                             * logical concept group.
                             */

                            'unresolved_requirements',
                                COALESCE(
                                    (
                                        SELECT
                                            jsonb_agg(
                                                jsonb_build_object(
                                                    'requirement_mention_id',
                                                        r.requirement_mention_id,

                                                    'type',
                                                        r.requirement_type,

                                                    'level',
                                                        r.requirement_level,

                                                    'text',
                                                        r.raw_text,

                                                    'status',
                                                        checks
                                                        .assessment_status,

                                                    'explanation',
                                                        checks
                                                        .explanation
                                                )

                                                ORDER BY
                                                    CASE
                                                        WHEN
                                                            r.requirement_level =
                                                            'required'
                                                        THEN 1

                                                        WHEN
                                                            r.requirement_level =
                                                            'preferred'
                                                        THEN 2

                                                        ELSE 3
                                                    END,

                                                    r.requirement_mention_id
                                            )

                                        FROM
                                            job_profile_requirement_checks
                                            checks

                                        JOIN
                                            job_requirement_mentions r

                                            ON
                                                r.requirement_mention_id =
                                                checks.requirement_mention_id

                                        WHERE
                                            checks.profile_id =
                                                :profile_id

                                            AND
                                            checks.fit_version =
                                                :profile_fit_version

                                            AND
                                            r.job_id =
                                                j.job_id

                                            AND
                                            r.extractor_version =
                                                :requirement_version
                                    ),

                                    '[]'::jsonb
                                )
                        )
                END AS profile_fit,


                CASE
                    WHEN EXISTS (
                        SELECT 1

                        FROM job_quality_flags dq

                        WHERE
                            dq.job_id =
                                j.job_id

                            AND
                            dq.generated_by =
                                'normalize_v1'

                            AND
                            dq.flag_code =
                                'insufficient_description'
                    )

                    THEN
                        jsonb_build_object(
                            'status',
                                'insufficient_job_data',

                            'reason',
                                (
                                    'The available job description '
                                    'does not contain enough '
                                    'information for a reliable '
                                    'eligibility assessment.'
                                )
                        )


                    WHEN
                        eligibility.job_id IS NULL

                    THEN NULL


                    ELSE
                        jsonb_build_object(
                            'status',
                                CASE
                                    WHEN
                                        eligibility.total_requirements =
                                        0

                                    THEN
                                        'no_explicit_checks'

                                    WHEN
                                        eligibility.not_satisfied_requirements >
                                        0

                                    THEN
                                        'not_satisfied'

                                    WHEN
                                        eligibility.needs_review_requirements >
                                        0

                                    THEN
                                        'needs_review'

                                    WHEN
                                        eligibility.candidate_requirements >
                                        0

                                    THEN
                                        'candidate'

                                    ELSE
                                        'satisfied'
                                END,

                            'total_requirements',
                                eligibility.total_requirements,

                            'satisfied',
                                eligibility.satisfied_requirements,

                            'candidate',
                                eligibility.candidate_requirements,

                            'not_satisfied',
                                eligibility.not_satisfied_requirements,

                            'needs_review',
                                eligibility.needs_review_requirements,

                            'checks',
                                COALESCE(
                                    (
                                        SELECT
                                            jsonb_agg(
                                                jsonb_build_object(
                                                    'fact_type',
                                                        er.fact_type,

                                                    'operator',
                                                        er.comparison_operator,

                                                    'requirement_value',
                                                        er.requirement_value,

                                                    'requirement_text',
                                                        rm.raw_text,

                                                    'status',
                                                        ec.assessment_status,

                                                    'explanation',
                                                        ec.explanation
                                                )

                                                ORDER BY
                                                    CASE
                                                        WHEN
                                                            ec.assessment_status =
                                                            'not_satisfied'
                                                        THEN 1

                                                        WHEN
                                                            ec.assessment_status =
                                                            'needs_review'
                                                        THEN 2

                                                        WHEN
                                                            ec.assessment_status =
                                                            'candidate'
                                                        THEN 3

                                                        ELSE 4
                                                    END,

                                                    er.eligibility_requirement_id
                                            )

                                        FROM
                                            job_profile_eligibility_checks
                                            ec

                                        JOIN
                                            job_eligibility_requirements er

                                            ON
                                                er.eligibility_requirement_id =
                                                ec.eligibility_requirement_id

                                        JOIN
                                            job_requirement_mentions rm

                                            ON
                                                rm.requirement_mention_id =
                                                er.requirement_mention_id

                                        WHERE
                                            ec.profile_id =
                                                :profile_id

                                            AND
                                            ec.assessment_version =
                                                'eligibility_v1'

                                            AND
                                            rm.job_id =
                                                j.job_id
                                    ),

                                    '[]'::jsonb
                                )
                        )
                END AS eligibility


            FROM search_jobs sj


            JOIN jobs j
                ON
                    j.job_id =
                    sj.job_id


            LEFT JOIN job_relevance_scores rel
                ON
                    rel.search_request_id =
                        :search_request_id

                    AND
                    rel.job_id =
                        j.job_id

                    AND
                    rel.scoring_method =
                        'semantic'

                    AND
                    rel.scoring_version =
                        'relevance_v1'


            LEFT JOIN job_profile_fit_summary fit
                ON
                    fit.profile_id =
                        :profile_id

                    AND
                    fit.job_id =
                        j.job_id

                    AND
                    fit.fit_version =
                        :profile_fit_version


            LEFT JOIN
                job_profile_eligibility_summary
                eligibility

                ON
                    eligibility.profile_id =
                        :profile_id

                    AND
                    eligibility.job_id =
                        j.job_id

                    AND
                    eligibility.assessment_version =
                        'eligibility_v1'


            ORDER BY

                EXISTS (
                    SELECT 1

                    FROM job_quality_flags dq

                    WHERE
                        dq.job_id =
                            j.job_id

                        AND
                        dq.generated_by =
                            'normalize_v1'

                        AND
                        dq.flag_code =
                            'insufficient_description'
                ) ASC,

                rel.combined_score
                    DESC NULLS LAST,

                sj.provider_rank
                    ASC NULLS LAST,

                j.job_id ASC;
            """
        ),
        {
            "search_request_id":
                search_request_id,

            "profile_id":
                profile_id,

            "profile_fit_version":
                PROFILE_FIT_VERSION,

            "requirement_version":
                REQUIREMENT_VERSION,

            "concept_version":
                CONCEPT_VERSION,
        },
    ).mappings().all()


    return [
        dict(row)
        for row in rows
    ]


@router.get("/quota")
def search_quota(
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    return get_search_quota(
        profile.profile_id,
        DATABASE_URL,
    )


@router.post("")
def search_jobs(
    request: JobSearchRequest,

    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    providers = list(
        dict.fromkeys(
            request.providers
        )
    )


    provider_available = (
        (
            "serpapi" in providers

            and bool(
                os.getenv(
                    "SERPAPI_API_KEY"
                )
            )
        )

        or

        (
            "jooble" in providers

            and bool(
                os.getenv(
                    "JOOBLE_API_KEY"
                )
            )
        )
    )


    if not provider_available:

        raise HTTPException(
            status_code=
                status.HTTP_503_SERVICE_UNAVAILABLE,

            detail=(
                "No requested job search "
                "provider is configured"
            ),
        )


    quota = reserve_search_slot(
        profile.profile_id,
        DATABASE_URL,
    )


    if not quota["allowed"]:

        raise HTTPException(
            status_code=
                status.HTTP_429_TOO_MANY_REQUESTS,

            detail={
                "message":
                    "Search quota exhausted",

                "limit":
                    quota["limit"],

                "remaining":
                    0,
            },
        )


    try:

        result = run_job_search(
            query=
                request.query,

            location=
                request.location,

            country=
                request.country,

            providers=
                providers,

            pages=
                1,

            database_url=
                DATABASE_URL,
        )


        search_request_id = (
            result[
                "search_request_id"
            ]
        )


        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    INSERT INTO
                        user_search_requests (
                            search_request_id,
                            profile_id
                        )

                    VALUES (
                        :search_request_id,
                        :profile_id
                    )

                    ON CONFLICT (
                        search_request_id
                    )

                    DO NOTHING;
                    """
                ),
                {
                    "search_request_id":
                        search_request_id,

                    "profile_id":
                        profile.profile_id,
                },
            )


        normalize_jobs(
            database_url=
                DATABASE_URL,

            search_request_id=
                search_request_id,
        )


        rank_search(
            search_request_id=
                search_request_id,

            database_url=
                DATABASE_URL,
        )


        extract_job_requirements(
            database_url=
                DATABASE_URL,

            search_request_id=
                search_request_id,
        )


        build_requirement_concepts(
            database_url=
                DATABASE_URL,

            search_request_id=
                search_request_id,
        )


        analysis = (
            refresh_search_assessments(
                profile_id=
                    profile.profile_id,

                search_request_id=
                    search_request_id,
            )
        )


    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail="Job search failed",
        ) from exc


    return {
        "search":
            result,

        "analysis":
            analysis,

        "quota": {
            "limit":
                quota["limit"],

            "used":
                quota["used"],

            "remaining":
                quota["remaining"],
        },
    }


@router.get("/latest/results")
def latest_search_results(
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    with engine.connect() as connection:

        latest_search = (
            connection.execute(
                text(
                    """
                    SELECT
                        search_request_id

                    FROM
                        user_search_requests

                    WHERE
                        profile_id =
                            :profile_id

                    ORDER BY
                        created_at DESC

                    LIMIT 1;
                    """
                ),
                {
                    "profile_id":
                        profile.profile_id,
                },
            )
            .mappings()
            .one_or_none()
        )


        if latest_search is None:

            return {
                "search_request_id":
                    None,

                "count":
                    0,

                "jobs":
                    [],
            }


        search_request_id = (
            latest_search[
                "search_request_id"
            ]
        )


        jobs = fetch_search_results(
            connection=
                connection,

            search_request_id=
                search_request_id,

            profile_id=
                profile.profile_id,
        )


    return {
        "search_request_id":
            search_request_id,

        "count":
            len(jobs),

        "jobs":
            jobs,
    }


@router.post("/latest/analyze")
def analyze_latest_search(
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    with engine.connect() as connection:

        latest_search = (
            connection.execute(
                text(
                    """
                    SELECT
                        search_request_id

                    FROM
                        user_search_requests

                    WHERE
                        profile_id =
                            :profile_id

                    ORDER BY
                        created_at DESC

                    LIMIT 1;
                    """
                ),
                {
                    "profile_id":
                        profile.profile_id,
                },
            )
            .mappings()
            .one_or_none()
        )


    if latest_search is None:

        raise HTTPException(
            status_code=404,
            detail="No job search found",
        )


    search_request_id = (
        latest_search[
            "search_request_id"
        ]
    )


    try:

        analysis = (
            refresh_search_assessments(
                profile_id=
                    profile.profile_id,

                search_request_id=
                    search_request_id,
            )
        )


    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail="Job analysis failed",
        ) from exc


    return {
        "search_request_id":
            search_request_id,

        "analysis":
            analysis,
    }


@router.get(
    "/{search_request_id}/results"
)
def search_results(
    search_request_id: int,

    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    with engine.connect() as connection:

        ownership = (
            connection.execute(
                text(
                    """
                    SELECT 1

                    FROM
                        user_search_requests

                    WHERE
                        search_request_id =
                            :search_request_id

                        AND
                        profile_id =
                            :profile_id;
                    """
                ),
                {
                    "search_request_id":
                        search_request_id,

                    "profile_id":
                        profile.profile_id,
                },
            )
            .first()
        )


        if ownership is None:

            raise HTTPException(
                status_code=404,
                detail="Search not found",
            )


        jobs = fetch_search_results(
            connection=
                connection,

            search_request_id=
                search_request_id,

            profile_id=
                profile.profile_id,
        )


    return {
        "search_request_id":
            search_request_id,

        "count":
            len(jobs),

        "jobs":
            jobs,
    }