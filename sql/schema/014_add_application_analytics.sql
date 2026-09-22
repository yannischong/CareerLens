CREATE OR REPLACE VIEW opportunity_stage_history AS

WITH event_rollup AS (
    SELECT
        opportunity_id,

        MIN(event_at) FILTER (
            WHERE to_status = 'applied'
        ) AS status_applied_at,

        MIN(event_at) FILTER (
            WHERE
                to_status = 'oa'
                OR event_type = 'oa'
        ) AS first_oa_at,

        MIN(event_at) FILTER (
            WHERE
                to_status = 'interview'
                OR event_type = 'interview'
        ) AS first_interview_at,

        MIN(event_at) FILTER (
            WHERE
                to_status = 'offer'
                OR event_type = 'offer'
        ) AS first_offer_at,

        MIN(event_at) FILTER (
            WHERE
                to_status = 'rejected'
                OR event_type = 'rejection'
        ) AS first_rejection_at,

        MIN(event_at) FILTER (
            WHERE
                to_status = 'withdrawn'
                OR event_type = 'withdrawal'
        ) AS first_withdrawal_at,

        MIN(event_at) FILTER (
            WHERE
                event_type IN (
                    'oa',
                    'interview',
                    'offer',
                    'rejection'
                )
                OR to_status IN (
                    'oa',
                    'interview',
                    'offer',
                    'rejected'
                )
        ) AS first_response_at

    FROM opportunity_events

    GROUP BY opportunity_id
)

SELECT
    o.opportunity_id,
    o.profile_id,
    o.job_id,
    o.source_search_request_id,
    o.current_status,
    o.priority,
    o.created_at AS tracked_at,

    COALESCE(
        a.submitted_at,
        er.status_applied_at
    ) AS applied_at,

    er.first_oa_at,
    er.first_interview_at,
    er.first_offer_at,
    er.first_rejection_at,
    er.first_withdrawal_at,
    er.first_response_at,

    a.application_id,
    a.resume_id,
    a.application_method,
    a.referral_used,
    a.cover_letter_used

FROM opportunities o

LEFT JOIN applications a
    ON o.opportunity_id =
       a.opportunity_id

LEFT JOIN event_rollup er
    ON o.opportunity_id =
       er.opportunity_id;

CREATE OR REPLACE VIEW opportunity_analytics AS

SELECT
    h.*,

    j.raw_title,
    j.raw_company_name,
    j.source,

    sr.query_text AS search_query,

    (h.applied_at IS NOT NULL)
        AS ever_applied,

    (
        h.first_oa_at IS NOT NULL
        OR h.current_status = 'oa'
    ) AS ever_oa,

    (
        h.first_interview_at IS NOT NULL
        OR h.current_status IN (
            'interview',
            'offer'
        )
    ) AS ever_interview,

    (
        h.first_offer_at IS NOT NULL
        OR h.current_status = 'offer'
    ) AS ever_offer,

    (
        h.first_rejection_at IS NOT NULL
        OR h.current_status = 'rejected'
    ) AS ever_rejected,

    (
        h.first_withdrawal_at IS NOT NULL
        OR h.current_status = 'withdrawn'
    ) AS ever_withdrawn,


    CASE
        WHEN
            h.applied_at IS NOT NULL
            AND h.first_response_at IS NOT NULL
            AND h.first_response_at >= h.applied_at

        THEN
            EXTRACT(
                EPOCH FROM (
                    h.first_response_at
                    - h.applied_at
                )
            ) / 86400.0
    END AS days_to_first_response,


    CASE
        WHEN
            h.applied_at IS NOT NULL
            AND h.first_interview_at IS NOT NULL
            AND h.first_interview_at >= h.applied_at

        THEN
            EXTRACT(
                EPOCH FROM (
                    h.first_interview_at
                    - h.applied_at
                )
            ) / 86400.0
    END AS days_to_interview,


    CASE
        WHEN
            h.applied_at IS NOT NULL
            AND h.first_offer_at IS NOT NULL
            AND h.first_offer_at >= h.applied_at

        THEN
            EXTRACT(
                EPOCH FROM (
                    h.first_offer_at
                    - h.applied_at
                )
            ) / 86400.0
    END AS days_to_offer

FROM opportunity_stage_history h

JOIN jobs j
    ON h.job_id = j.job_id

LEFT JOIN search_requests sr
    ON h.source_search_request_id =
       sr.search_request_id;

CREATE OR REPLACE VIEW application_funnel_summary AS

SELECT
    profile_id,

    COUNT(*) AS tracked_opportunities,

    COUNT(*) FILTER (
        WHERE ever_applied
    ) AS applications,

    COUNT(*) FILTER (
        WHERE ever_oa
    ) AS oa_reached,

    COUNT(*) FILTER (
        WHERE ever_interview
    ) AS interviews_reached,

    COUNT(*) FILTER (
        WHERE ever_offer
    ) AS offers_received,

    COUNT(*) FILTER (
        WHERE ever_rejected
    ) AS rejections,


    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE ever_oa
            )
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE ever_applied
                ),
                0
            )
        )::numeric,
        2
    ) AS application_to_oa_pct,


    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE ever_interview
            )
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE ever_applied
                ),
                0
            )
        )::numeric,
        2
    ) AS application_to_interview_pct,


    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE ever_offer
            )
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE ever_applied
                ),
                0
            )
        )::numeric,
        2
    ) AS application_to_offer_pct,


    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE ever_offer
            )
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE ever_interview
                ),
                0
            )
        )::numeric,
        2
    ) AS interview_to_offer_pct,


    ROUND(
        AVG(days_to_first_response)
            FILTER (
                WHERE days_to_first_response
                      IS NOT NULL
            )::numeric,
        2
    ) AS avg_days_to_first_response,


    ROUND(
        AVG(days_to_interview)
            FILTER (
                WHERE days_to_interview
                      IS NOT NULL
            )::numeric,
        2
    ) AS avg_days_to_interview

FROM opportunity_analytics

GROUP BY profile_id;

CREATE OR REPLACE VIEW resume_application_performance AS

SELECT
    oa.profile_id,
    rd.resume_id,
    rd.original_filename,

    COUNT(*) AS applications,

    COUNT(*) FILTER (
        WHERE oa.ever_oa
    ) AS oa_reached,

    COUNT(*) FILTER (
        WHERE oa.ever_interview
    ) AS interviews_reached,

    COUNT(*) FILTER (
        WHERE oa.ever_offer
    ) AS offers_received,


    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE oa.ever_interview
            )
            / NULLIF(
                COUNT(*),
                0
            )
        )::numeric,
        2
    ) AS interview_rate_pct,


    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE oa.ever_offer
            )
            / NULLIF(
                COUNT(*),
                0
            )
        )::numeric,
        2
    ) AS offer_rate_pct,


    ROUND(
        AVG(
            oa.days_to_first_response
        ) FILTER (
            WHERE
                oa.days_to_first_response
                IS NOT NULL
        )::numeric,
        2
    ) AS avg_days_to_response

FROM opportunity_analytics oa

JOIN resume_documents rd
    ON oa.resume_id =
       rd.resume_id

WHERE oa.ever_applied

GROUP BY
    oa.profile_id,
    rd.resume_id,
    rd.original_filename;

CREATE OR REPLACE VIEW search_query_performance AS

SELECT
    profile_id,
    search_query,

    COUNT(*) FILTER (
        WHERE ever_applied
    ) AS applications,

    COUNT(*) FILTER (
        WHERE ever_oa
    ) AS oa_reached,

    COUNT(*) FILTER (
        WHERE ever_interview
    ) AS interviews_reached,

    COUNT(*) FILTER (
        WHERE ever_offer
    ) AS offers_received,


    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE ever_interview
            )
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE ever_applied
                ),
                0
            )
        )::numeric,
        2
    ) AS interview_rate_pct

FROM opportunity_analytics

WHERE search_query IS NOT NULL

GROUP BY
    profile_id,
    search_query;

CREATE OR REPLACE VIEW company_application_performance AS

SELECT
    profile_id,
    raw_company_name,

    COUNT(*) FILTER (
        WHERE ever_applied
    ) AS applications,

    COUNT(*) FILTER (
        WHERE ever_oa
    ) AS oa_reached,

    COUNT(*) FILTER (
        WHERE ever_interview
    ) AS interviews_reached,

    COUNT(*) FILTER (
        WHERE ever_offer
    ) AS offers_received,

    COUNT(*) FILTER (
        WHERE ever_rejected
    ) AS rejections

FROM opportunity_analytics

GROUP BY
    profile_id,
    raw_company_name;