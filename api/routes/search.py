import hashlib
import json
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
from src.user_profile.map_profile_concepts import (
    map_profile_concepts,
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
from src.services.provider_analysis_cache_service import (
    get_cached_job_analysis,
    get_cached_profile_analysis,
    get_cached_profile_analyses_for_search,
    store_job_analysis,
    store_profile_analysis,
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


    profile_concepts = (
        map_profile_concepts(
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

        "profile_concepts":
            profile_concepts,

        "profile_fit":
            fit_result,

        "eligibility":
            eligibility_result,
    }


def _provider_match_percentage(
    profile_fit,
):
    if (
        not isinstance(
            profile_fit,
            dict,
        )
        or profile_fit.get(
            "status"
        )
        != "assessed"
    ):
        return None

    groups = (
        profile_fit.get(
            "groups"
        )
        or []
    )

    level_weights = {
        "required": 2.0,
        "preferred": 1.0,
        "unknown": 1.0,
    }

    status_credits = {
        "evidenced": 1.0,
        "claimed_only": 0.8,
        "candidate": 0.5,
        "needs_review": 0.25,
        "gap": 0.0,
    }

    if groups:
        total_weight = 0.0
        earned_weight = 0.0

        for group in groups:
            weight = level_weights.get(
                group.get(
                    "level"
                ),
                1.0,
            )

            credit = status_credits.get(
                group.get(
                    "status"
                ),
                0.0,
            )

            total_weight += weight
            earned_weight += (
                weight
                * credit
            )

        if total_weight > 0:
            return round(
                100.0
                * earned_weight
                / total_weight,
                1,
            )

    total_groups = int(
        profile_fit.get(
            "total_groups",
            0,
        )
        or 0
    )

    if total_groups <= 0:
        return None

    earned = (
        float(
            profile_fit.get(
                "group_evidenced",
                0,
            )
            or 0
        )
        + 0.8
        * float(
            profile_fit.get(
                "group_claimed_only",
                0,
            )
            or 0
        )
        + 0.5
        * float(
            profile_fit.get(
                "group_candidate",
                0,
            )
            or 0
        )
        + 0.25
        * float(
            profile_fit.get(
                "needs_review",
                0,
            )
            or 0
        )
    )

    return round(
        100.0
        * earned
        / total_groups,
        1,
    )


def _provider_job_content_hash(
    job,
    analysis_text=None,
):
    if analysis_text is None:
        analysis_text = (
            _provider_analysis_text(
                job
            )
        )

    return hashlib.sha256(
        str(
            analysis_text
            or ""
        ).encode(
            "utf-8"
        )
    ).hexdigest()


def _latest_resume_id(
    connection,
    profile_id,
):
    return (
        connection.execute(
            text(
                """
                    SELECT
                        resume_id

                    FROM
                        resume_documents

                    WHERE
                        profile_id =
                            :profile_id

                    ORDER BY
                        resume_id DESC

                    LIMIT 1;
                """
            ),
            {
                "profile_id":
                    profile_id,
            },
        )
        .scalar_one_or_none()
    )


def _provider_result_sort_key(
    job,
):
    search_relevance = (
        job.get(
            "search_relevance"
        )
    )

    relevance_rank = (
        job.get(
            "relevance_rank"
        )
    )

    provider_rank = (
        job.get(
            "provider_rank"
        )
    )

    # CareerLens ranks provider results by how relevant they are to the user's
    # search. Resume match is intentionally informational only: its purpose is
    # to show what the user may want to tailor, not to hide relevant jobs.
    return (
        1
        if search_relevance is None
        else 0,

        -float(
            search_relevance
            or 0
        ),

        int(
            relevance_rank
            if relevance_rank
            is not None
            else 1_000_000
        ),

        int(
            provider_rank
            if provider_rank
            is not None
            else 1_000_000
        ),

        int(
            job[
                "job_id"
            ]
        ),
    )


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
                j.requirements_text,
                j.education_requirements,
                j.experience_requirements,
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
                                        req.structured_value,

                                    'concepts',
                                        COALESCE(
                                            (
                                                SELECT
                                                    jsonb_agg(
                                                        jsonb_build_object(
                                                            'name',
                                                                concept.canonical_name,

                                                            'type',
                                                                concept.concept_type,

                                                            'confidence',
                                                                link.confidence
                                                        )

                                                        ORDER BY
                                                            concept.canonical_name
                                                    )

                                                FROM
                                                    job_requirement_concepts link

                                                JOIN
                                                    requirement_concepts concept

                                                    ON
                                                        concept.concept_id =
                                                        link.concept_id

                                                WHERE
                                                    link.requirement_mention_id =
                                                    req.requirement_mention_id

                                                    AND
                                                    link.extractor_version =
                                                    :concept_version
                                            ),

                                            '[]'::jsonb
                                        )
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


    jobs = [
        dict(row)
        for row in rows
    ]

    resume_id = (
        _latest_resume_id(
            connection,
            profile_id,
        )
    )

    cached_analyses = (
        get_cached_profile_analyses_for_search(
            connection,
            profile_id=
                profile_id,
            resume_id=
                resume_id,
            search_request_id=
                search_request_id,
        )
    )

    for job in jobs:
        job_hash = (
            _provider_job_content_hash(
                job
            )
        )

        cached = (
            cached_analyses.get(
                (
                    int(
                        job[
                            "job_id"
                        ]
                    ),
                    job_hash,
                )
            )
        )

        job[
            "ai_analysis_cached"
        ] = False

        job[
            "analysis_method"
        ] = None

        if cached:
            payload = (
                cached.get(
                    "analysis_payload"
                )
                or {}
            )

            cached_requirements = (
                payload.get(
                    "requirements"
                )
                or []
            )

            cached_profile_fit = (
                payload.get(
                    "profile_fit"
                )
            )

            if cached_requirements:
                job[
                    "requirements"
                ] = cached_requirements

            if cached_profile_fit:
                job[
                    "profile_fit"
                ] = cached_profile_fit

            cached_percentage = (
                cached.get(
                    "resume_match_percentage"
                )
            )

            job[
                "resume_match_percentage"
            ] = (
                float(
                    cached_percentage
                )
                if cached_percentage
                is not None
                else None
            )

            job[
                "ai_analysis_cached"
            ] = True

            job[
                "analysis_method"
            ] = payload.get(
                "analysis_method"
            )

        else:
            job[
                "resume_match_percentage"
            ] = (
                _provider_match_percentage(
                    job.get(
                        "profile_fit"
                    )
                )
            )

        for internal_field in (
            "requirements_text",
            "education_requirements",
            "experience_requirements",
        ):
            job.pop(
                internal_field,
                None,
            )

    jobs.sort(
        key=
            _provider_result_sort_key
    )

    return jobs


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




def _provider_analysis_text(job):
    """Build the richest provider-side text before external-page enrichment.

    Google Jobs/SerpAPI can expose qualifications and responsibilities under
    source_metadata even when the visible description is shortened. Including
    them here prevents the AI from being limited to the card snippet.
    """

    parts = []

    def add(value, heading=None):
        value = str(value or "").strip()
        if not value:
            return

        combined = "\n\n".join(parts).casefold()
        if value.casefold() in combined:
            return

        parts.append(
            f"{heading}\n{value}"
            if heading
            else value
        )

    description = str(job.get("description") or "").strip()
    add(description)

    for heading, key in (
        ("Requirements", "requirements_text"),
        ("Education requirements", "education_requirements"),
        ("Experience requirements", "experience_requirements"),
    ):
        add(job.get(key), heading)

    metadata = job.get("source_metadata") or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}

    if isinstance(metadata, dict):
        for key, heading in (
            ("description", None),
            ("job_description", "Job description"),
            ("jobDescription", "Job description"),
            ("qualifications", "Qualifications"),
            ("requirements", "Requirements"),
            ("responsibilities", "Responsibilities"),
            ("skills", "Skills"),
        ):
            add(metadata.get(key), heading)

        for highlights_key in ("job_highlights", "highlights"):
            highlights = metadata.get(highlights_key) or []
            if not isinstance(highlights, list):
                continue

            for block in highlights:
                if not isinstance(block, dict):
                    continue

                heading = str(
                    block.get("title")
                    or block.get("heading")
                    or "Job details"
                ).strip()

                items = block.get("items") or block.get("content") or []
                if isinstance(items, list):
                    body = "\n".join(
                        str(item).strip()
                        for item in items
                        if str(item).strip()
                    )
                else:
                    body = str(items or "").strip()

                add(body, heading)

    return "\n\n".join(parts).strip()

def _provider_level_rank(
    level,
):
    return {
        "unknown": 1,
        "preferred": 2,
        "required": 3,
    }.get(
        level,
        0,
    )


def _provider_resume_status(
    result,
):
    if not result:
        return "needs_review"

    status = result.get(
        "status"
    )

    if status == "evidenced":
        return "evidenced"

    if status == "claimed_only":
        return "claimed_only"

    if status == "candidate":
        return "candidate"

    if status == "unsupported":
        return "gap"

    return "needs_review"


def _provider_status_explanation(
    status,
):
    if status == "evidenced":
        return (
            "CareerCompass found concrete resume evidence "
            "supporting this skill."
        )

    if status == "claimed_only":
        return (
            "The skill is mentioned on your resume, but the "
            "resume does not clearly demonstrate its use."
        )

    if status == "candidate":
        return (
            "Related resume evidence was found, but the exact "
            "skill is only partially supported."
        )

    if status == "gap":
        return (
            "CareerCompass did not find supporting evidence for "
            "this skill in your uploaded resume."
        )

    return (
        "CareerCompass could not confidently determine resume "
        "support for this skill."
    )


def _build_provider_profile_fit(
    job_id,
    skills,
    model_results,
):
    if not skills or not model_results:
        return None

    concepts = []
    groups = []

    for skill in skills:
        concept_id = skill[
            "concept_id"
        ]

        model_result = (
            model_results.get(
                concept_id
            )
        )

        status = (
            _provider_resume_status(
                model_result
            )
        )

        evidence = (
            model_result.get(
                "evidence"
            )
            if model_result
            else None
        )

        model_confidence = (
            model_result.get(
                "confidence"
            )
            if model_result
            else None
        )

        if status == "evidenced":
            claim_status = "confirmed"
            evidence_status = "confirmed"

        elif status == "claimed_only":
            claim_status = "confirmed"
            evidence_status = "not_confirmed"

        elif status == "candidate":
            claim_status = "candidate"
            evidence_status = "candidate"

        else:
            claim_status = "not_confirmed"
            evidence_status = "not_confirmed"

        concept = {
            "concept_id":
                concept_id,

            "name":
                skill[
                    "name"
                ],

            "type":
                skill[
                    "type"
                ],

            "level":
                skill[
                    "level"
                ],

            "fit_status":
                status,

            "claim_status":
                claim_status,

            "evidence_status":
                evidence_status,

            "model_evidence":
                evidence,

            "model_confidence":
                model_confidence,
        }

        concepts.append(
            concept
        )

        matched = status in {
            "evidenced",
            "claimed_only",
            "candidate",
        }

        groups.append(
            {
                "requirement_mention_id":
                    (
                        int(job_id)
                        * 100000
                        + concept_id
                    ),

                "type":
                    "skill",

                "level":
                    skill[
                        "level"
                    ],

                "text":
                    skill[
                        "source_text"
                    ],

                "operator":
                    "all_of",

                "is_open":
                    False,

                "status":
                    status,

                "explanation":
                    _provider_status_explanation(
                        status
                    ),

                "matched_concept_id":
                    (
                        concept_id
                        if matched
                        else None
                    ),

                "matched_concept_name":
                    (
                        skill[
                            "name"
                        ]
                        if matched
                        else None
                    ),

                "concepts": [
                    {
                        "concept_id":
                            concept_id,

                        "name":
                            skill[
                                "name"
                            ],

                        "claim_status":
                            claim_status,

                        "evidence_status":
                            evidence_status,

                        "fit_status":
                            status,

                        "model_evidence":
                            evidence,

                        "model_confidence":
                            model_confidence,
                    }
                ],
            }
        )

    statuses = [
        group[
            "status"
        ]
        for group in groups
    ]

    required_groups = [
        group
        for group in groups
        if group[
            "level"
        ] == "required"
    ]

    preferred_groups = [
        group
        for group in groups
        if group[
            "level"
        ] == "preferred"
    ]

    unknown_groups = [
        group
        for group in groups
        if group[
            "level"
        ] == "unknown"
    ]

    return {
        "status":
            "assessed",

        "model_version":
            "provider_model_v1",

        "total_concepts":
            len(concepts),

        "required_concepts":
            len(required_groups),

        "preferred_concepts":
            len(preferred_groups),

        "unknown_level_concepts":
            len(unknown_groups),

        "evidenced":
            statuses.count(
                "evidenced"
            ),

        "claimed_only":
            statuses.count(
                "claimed_only"
            ),

        "candidate":
            statuses.count(
                "candidate"
            ),

        "gaps":
            statuses.count(
                "gap"
            ),

        "required_candidates":
            sum(
                1
                for group in required_groups
                if group[
                    "status"
                ] == "candidate"
            ),

        "required_gaps":
            sum(
                1
                for group in required_groups
                if group[
                    "status"
                ] == "gap"
            ),

        "total_groups":
            len(groups),

        "required_groups":
            len(required_groups),

        "preferred_groups":
            len(preferred_groups),

        "unknown_groups":
            len(unknown_groups),

        "group_evidenced":
            statuses.count(
                "evidenced"
            ),

        "group_claimed_only":
            statuses.count(
                "claimed_only"
            ),

        "group_candidate":
            statuses.count(
                "candidate"
            ),

        "group_gaps":
            statuses.count(
                "gap"
            ),

        "required_candidate_groups":
            sum(
                1
                for group in required_groups
                if group[
                    "status"
                ] == "candidate"
            ),

        "required_gap_groups":
            sum(
                1
                for group in required_groups
                if group[
                    "status"
                ] == "gap"
            ),

        "needs_review":
            statuses.count(
                "needs_review"
            ),

        "concepts":
            concepts,

        "groups":
            groups,

        "unresolved_requirements":
            [],
    }


def _extract_provider_job_analysis(
    job_id,
    analysis_text,
):
    # Lazy imports keep model code outside FastAPI startup.
    from src.extraction.model_skill_extractor import (
        enrich_manual_requirement_mentions,
    )
    from src.extraction.rules import (
        extract_requirements,
    )
    from src.taxonomy.atomic import (
        extract_atomic_concepts,
    )

    mentions = extract_requirements(
        analysis_text,
        source_field="description",
    )

    mentions = (
        enrich_manual_requirement_mentions(
            analysis_text,
            mentions,
            source_field="description",
        )
    )

    model_skill_used = any(
        bool(
            (
                mention.structured_value
                or {}
            ).get(
                "model_skill_processed"
            )
        )
        for mention in mentions
    )

    requirements = []
    skill_by_key = {}

    for index, mention in enumerate(
        mentions,
        start=1,
    ):
        candidates = (
            extract_atomic_concepts(
                mention.raw_text,
                mention.requirement_type,
                structured_value=(
                    mention.structured_value
                ),
            )
        )

        candidates = [
            candidate
            for candidate in candidates
            if candidate.get(
                "concept_type"
            )
            in {
                "hard_skill",
                "soft_skill",
            }
        ]

        if not candidates:
            continue

        requirement_concepts = []

        for candidate in candidates:
            normalized_key = (
                candidate.get(
                    "normalized_key"
                )
                or ""
            )

            concept_type = (
                candidate.get(
                    "concept_type"
                )
            )

            canonical_name = (
                candidate.get(
                    "raw_text"
                )
                or normalized_key
            )

            try:
                confidence = float(
                    candidate.get(
                        "confidence",
                        0.0,
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                confidence = 0.0

            if not normalized_key:
                continue

            key = (
                concept_type,
                normalized_key,
            )

            existing = (
                skill_by_key.get(
                    key
                )
            )

            skill = {
                "name":
                    canonical_name,

                "type":
                    concept_type,

                "level":
                    mention.requirement_level,

                "confidence":
                    confidence,

                "source_text":
                    mention.raw_text,

                "section_type":
                    (
                        mention.structured_value
                        or {}
                    ).get(
                        "section_type",
                        "other",
                    ),
            }

            if (
                existing is None
                or _provider_level_rank(
                    skill[
                        "level"
                    ]
                )
                > _provider_level_rank(
                    existing[
                        "level"
                    ]
                )
                or (
                    _provider_level_rank(
                        skill[
                            "level"
                        ]
                    )
                    == _provider_level_rank(
                        existing[
                            "level"
                        ]
                    )
                    and skill[
                        "confidence"
                    ]
                    > existing[
                        "confidence"
                    ]
                )
            ):
                skill_by_key[
                    key
                ] = skill

            requirement_concepts.append(
                {
                    "name":
                        canonical_name,

                    "type":
                        concept_type,

                    "confidence":
                        confidence,
                }
            )

        if not requirement_concepts:
            continue

        requirements.append(
            {
                "id":
                    (
                        int(job_id)
                        * 100000
                        + index
                    ),

                "type":
                    mention.requirement_type,

                "level":
                    mention.requirement_level,

                "text":
                    mention.raw_text,

                "structured_value":
                    mention.structured_value,

                "concepts":
                    requirement_concepts,
            }
        )

    skills = list(
        skill_by_key.values()
    )

    skills.sort(
        key=lambda item: (
            -_provider_level_rank(
                item[
                    "level"
                ]
            ),
            item[
                "type"
            ],
            item[
                "name"
            ].casefold(),
        )
    )

    for concept_id, skill in enumerate(
        skills,
        start=1,
    ):
        skill[
            "concept_id"
        ] = concept_id

    analysis_method = (
        "model_assisted_on_demand_v2"
        if model_skill_used
        else "rule_fallback_on_demand_v2"
    )

    return (
        analysis_method,
        requirements,
        skills,
    )


@router.post(
    "/jobs/{job_id}/analyze"
)
def analyze_provider_job(
    job_id: int,

    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    """Analyze one provider job on demand and reuse persistent cached results.

    The job-skill extraction cache is shared across users for the same job
    content. Resume matching is cached per profile + resume, so replacing a
    resume invalidates only the resume-fit layer while preserving job
    extraction.
    """

    with engine.connect() as connection:
        job = (
            connection.execute(
                text(
                    """
                    SELECT
                        j.job_id,
                        j.raw_title,
                        j.raw_company_name,
                        j.location_raw,
                        j.source,
                        j.source_job_id,
                        j.job_url,
                        j.source_metadata,
                        j.description,
                        j.requirements_text,
                        j.education_requirements,
                        j.experience_requirements

                    FROM jobs AS j

                    WHERE
                        j.job_id =
                            :job_id

                        AND EXISTS (
                            SELECT 1

                            FROM
                                source_search_results AS ssres

                            JOIN
                                source_search_runs AS ssr

                                ON
                                    ssr.source_search_run_id =
                                        ssres.source_search_run_id

                            JOIN
                                user_search_requests AS usr

                                ON
                                    usr.search_request_id =
                                        ssr.search_request_id

                            WHERE
                                ssres.job_id =
                                    j.job_id

                                AND
                                usr.profile_id =
                                    :profile_id
                        );
                    """
                ),
                {
                    "job_id":
                        job_id,

                    "profile_id":
                        profile.profile_id,
                },
            )
            .mappings()
            .one_or_none()
        )

        resume = (
            connection.execute(
                text(
                    """
                    SELECT
                        resume_id,
                        raw_text

                    FROM
                        resume_documents

                    WHERE
                        profile_id =
                            :profile_id

                    ORDER BY
                        resume_id DESC

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

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job result not found",
        )

    provider_text = (
        _provider_analysis_text(
            job
        )
    )

    # Import the page/ATS enrichment layer lazily so a problem in an
    # external-page integration can never prevent the FastAPI service from
    # binding its Render port during process startup.
    try:
        from src.services.job_posting_enrichment_service import (
            enrich_provider_job_description,
        )

        enrichment = (
            enrich_provider_job_description(
                dict(job),
                provider_text,
            )
        )
    except Exception as exc:
        print(
            "[CareerLens provider enrichment] "
            f"falling back to provider text: {exc}",
            flush=True,
        )

        enrichment = {
            "analysis_text": provider_text,
            "description_source": "provider",
            "description_completeness": (
                "partial"
                if len(provider_text) < 700
                else "likely_full"
            ),
            "provider_characters": len(provider_text),
            "analysis_characters": len(provider_text),
            "full_posting_retrieved": False,
            "fetch_attempted": False,
        }

    analysis_text = (
        enrichment.get(
            "analysis_text"
        )
        or provider_text
    )

    source_metadata = {
        "description_source":
            enrichment.get(
                "description_source",
                "provider",
            ),

        "description_completeness":
            enrichment.get(
                "description_completeness",
                "partial",
            ),

        "provider_description_characters":
            enrichment.get(
                "provider_characters",
                len(provider_text),
            ),

        "analysis_description_characters":
            enrichment.get(
                "analysis_characters",
                len(analysis_text),
            ),

        "full_posting_retrieved":
            bool(
                enrichment.get(
                    "full_posting_retrieved"
                )
            ),

        "original_source_url":
            enrichment.get(
                "original_source_url"
            ),

        "original_source_host":
            enrichment.get(
                "original_source_host"
            ),

        "source_resolution_method":
            enrichment.get(
                "source_resolution_method"
            ),

        "source_resolution_confidence":
            enrichment.get(
                "source_resolution_confidence"
            ),
    }

    # Persist a successfully resolved employer/ATS destination inside the
    # existing jobs.source_metadata JSONB. This avoids repeating the Jooble
    # outbound/SerpAPI source-resolution lookup on future opens.
    resolved_source_url = source_metadata.get(
        "original_source_url"
    )

    if (
        resolved_source_url
        and source_metadata.get(
            "full_posting_retrieved"
        )
    ):
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        UPDATE jobs

                        SET source_metadata =
                            COALESCE(
                                source_metadata,
                                '{}'::jsonb
                            )
                            || jsonb_build_object(
                                'resolved_source_url',
                                CAST(:resolved_source_url AS text),
                                'resolved_source_method',
                                CAST(:resolved_source_method AS text),
                                'resolved_source_host',
                                CAST(:resolved_source_host AS text),
                                'resolved_source_confidence',
                                CAST(:resolved_source_confidence AS numeric),
                                'resolved_source_at',
                                to_jsonb(NOW())
                            )

                        WHERE job_id = :job_id;
                        """
                    ),
                    {
                        "resolved_source_url":
                            resolved_source_url,

                        "resolved_source_method":
                            source_metadata.get(
                                "source_resolution_method"
                            )
                            or "resolved_original_source",

                        "resolved_source_host":
                            source_metadata.get(
                                "original_source_host"
                            )
                            or "",

                        "resolved_source_confidence":
                            source_metadata.get(
                                "source_resolution_confidence"
                            )
                            or 1.0,

                        "job_id":
                            job_id,
                    },
                )
        except Exception as exc:
            print(
                "[CareerLens source resolver] "
                f"could not persist resolved source for job {job_id}: {exc}",
                flush=True,
            )

    if not analysis_text:
        return {
            "job_id":
                job_id,

            "analysis_method":
                "insufficient_job_data",

            "requirements":
                [],

            "profile_fit":
                None,

            "resume_match_percentage":
                None,

            "cache_hit":
                "none",

            **source_metadata,
        }

    job_hash = (
        _provider_job_content_hash(
            job,
            analysis_text=analysis_text,
        )
    )

    resume_id = (
        resume[
            "resume_id"
        ]
        if resume is not None
        else None
    )

    resume_text = (
        resume[
            "raw_text"
        ]
        if resume is not None
        else None
    )

    # Fastest path: the exact job + exact latest resume were already analyzed.
    if resume_id is not None:
        with engine.connect() as connection:
            cached_profile = (
                get_cached_profile_analysis(
                    connection,
                    profile_id=
                        profile.profile_id,
                    job_id=
                        job_id,
                    resume_id=
                        resume_id,
                    job_content_hash=
                        job_hash,
                )
            )

        if cached_profile is not None:
            payload = dict(
                cached_profile.get(
                    "analysis_payload"
                )
                or {}
            )

            payload[
                "cache_hit"
            ] = "profile"

            cached_percentage = (
                cached_profile.get(
                    "resume_match_percentage"
                )
            )

            payload[
                "resume_match_percentage"
            ] = (
                float(
                    cached_percentage
                )
                if cached_percentage
                is not None
                else None
            )

            payload.update(
                source_metadata
            )

            return payload

    with engine.connect() as connection:
        cached_job = (
            get_cached_job_analysis(
                connection,
                job_id=
                    job_id,
                job_content_hash=
                    job_hash,
            )
        )

    if cached_job is not None:
        analysis_method = (
            cached_job[
                "analysis_method"
            ]
        )

        requirements = list(
            cached_job.get(
                "requirements"
            )
            or []
        )

        skills = list(
            cached_job.get(
                "skills"
            )
            or []
        )

        job_cache_hit = True

    else:
        try:
            (
                analysis_method,
                requirements,
                skills,
            ) = _extract_provider_job_analysis(
                job_id,
                analysis_text,
            )

        except Exception as exc:
            print(
                "[CareerLens provider analysis] "
                f"model/extraction failed for job {job_id}; "
                f"returning existing fallback analysis: {exc}",
                flush=True,
            )

            analysis_method = (
                "rule_fallback_after_analysis_error_v3"
            )
            requirements = []
            skills = []

        job_cache_hit = False

        # Only persist successful model-assisted extraction. A temporary model
        # outage may fall back to deterministic rules; caching that fallback
        # would prevent a later request from retrying the model.
        if analysis_method.startswith(
            "model_assisted"
        ):
            try:
                with engine.begin() as connection:
                    store_job_analysis(
                        connection,
                        job_id=
                            job_id,
                        job_content_hash=
                            job_hash,
                        analysis_method=
                            analysis_method,
                        requirements=
                            requirements,
                        skills=
                            skills,
                    )
            except Exception:
                pass

    model_results = {}
    resume_model_used = False

    if resume_text and skills:
        try:
            from src.user_profile.model_resume_matcher import (
                verify_resume_skills,
            )

            model_results = (
                verify_resume_skills(
                    resume_text,
                    [
                        {
                            "concept_id":
                                skill[
                                    "concept_id"
                                ],

                            "name":
                                skill[
                                    "name"
                                ],

                            "type":
                                skill[
                                    "type"
                                ],

                            "requirement_level":
                                skill[
                                    "level"
                                ],

                            "fit_status":
                                "gap",
                        }
                        for skill in skills
                    ],
                )
            )

            resume_model_used = bool(
                model_results
            )

        except Exception as exc:
            print(
                "[CareerLens provider resume model] "
                f"verification failed for job {job_id}: {exc}",
                flush=True,
            )
            model_results = {}
            resume_model_used = False

    profile_fit = (
        _build_provider_profile_fit(
            job_id,
            skills,
            model_results,
        )
        if resume_text
        else None
    )

    resume_match_percentage = (
        _provider_match_percentage(
            profile_fit
        )
    )

    response_payload = {
        "job_id":
            job_id,

        "analysis_method":
            analysis_method,

        "job_model_used":
            analysis_method.startswith(
                "model_assisted"
            ),

        "resume_model_used":
            resume_model_used,

        "requirements":
            requirements,

        "profile_fit":
            profile_fit,

        "resume_match_percentage":
            resume_match_percentage,

        "cache_hit":
            (
                "job"
                if job_cache_hit
                else "none"
            ),

        **source_metadata,
    }

    if (
        resume_id is not None
        and profile_fit is not None
        and analysis_method.startswith(
            "model_assisted"
        )
        and resume_model_used
    ):
        try:
            with engine.begin() as connection:
                store_profile_analysis(
                    connection,
                    profile_id=
                        profile.profile_id,
                    job_id=
                        job_id,
                    resume_id=
                        resume_id,
                    job_content_hash=
                        job_hash,
                    analysis_payload=
                        response_payload,
                    resume_match_percentage=
                        resume_match_percentage,
                )
        except Exception:
            pass

    return response_payload


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