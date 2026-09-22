import os
from datetime import datetime
from typing import Literal

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from api.profile import CurrentProfile, get_current_profile
from src.collection.database import create_database_engine
from src.services.job_fit_service import assess_job_fit


load_dotenv()

router = APIRouter(
    prefix="/api/opportunities",
    tags=["Opportunities"],
)

DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL")
engine = create_database_engine(DATABASE_URL)


OpportunityStatus = Literal[
    "discovered",
    "saved",
    "to_apply",
    "applied",
    "oa",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
    "closed",
]

OpportunityPriority = Literal[
    "low",
    "medium",
    "high",
]

ManualOpportunityEventType = Literal[
    "note",
    "deadline",
    "oa",
    "interview",
    "follow_up",
    "offer",
    "rejection",
    "withdrawal",
    "other",
]

EARLY_APPLICATION_STATUSES = {
    "discovered",
    "saved",
    "to_apply",
}


class CreateOpportunityRequest(BaseModel):
    job_id: int
    source_search_request_id: int | None = None
    priority: OpportunityPriority = "medium"
    notes: str | None = None


class UpdateOpportunityRequest(BaseModel):
    priority: OpportunityPriority | None = None
    notes: str | None = None


class UpdateStatusRequest(BaseModel):
    status: OpportunityStatus
    notes: str | None = None


class RecordApplicationRequest(BaseModel):
    resume_id: int | None = None
    application_url: str | None = None
    application_method: str | None = None
    referral_used: bool = False
    cover_letter_used: bool = False
    notes: str | None = None


class CreateOpportunityEventRequest(BaseModel):
    event_type: ManualOpportunityEventType
    event_at: datetime | None = None
    notes: str | None = None


def get_owned_opportunity(
    connection,
    opportunity_id: int,
    profile_id: int,
):
    opportunity = (
        connection.execute(
            text(
                """
                SELECT
                    opportunity_id,
                    profile_id,
                    job_id,
                    source_search_request_id,
                    current_status,
                    priority,
                    notes,
                    created_at,
                    updated_at
                FROM opportunities
                WHERE
                    opportunity_id = :opportunity_id
                    AND profile_id = :profile_id;
                """
            ),
            {
                "opportunity_id": opportunity_id,
                "profile_id": profile_id,
            },
        )
        .mappings()
        .one_or_none()
    )

    if opportunity is None:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found.",
        )

    return opportunity


def fetch_opportunity_detail(
    connection,
    opportunity_id: int,
    profile_id: int,
):
    row = (
        connection.execute(
            text(
                """
                SELECT
                    o.opportunity_id,
                    o.profile_id,
                    o.job_id,
                    o.source_search_request_id,
                    o.current_status,
                    o.priority,
                    o.notes,
                    o.created_at,
                    o.updated_at,

                    j.raw_title,
                    j.raw_company_name,
                    j.location_raw,
                    j.job_url,
                    j.source,
                    j.date_posted,
                    j.derived_posted_date,

                    sr.query_text AS search_query,

                    a.application_id,
                    a.resume_id,
                    a.application_url,
                    a.application_method,
                    a.submitted_at,
                    a.referral_used,
                    a.cover_letter_used,
                    a.notes AS application_notes,

                    osh.tracked_at,
                    osh.applied_at,
                    osh.first_oa_at,
                    osh.first_interview_at,
                    osh.first_offer_at,
                    osh.first_rejection_at,
                    osh.first_withdrawal_at,
                    osh.first_response_at,

                    next_event.next_event_type,
                    next_event.next_event_at,
                    next_event.next_event_notes

                FROM opportunities o

                JOIN jobs j
                    ON j.job_id = o.job_id

                LEFT JOIN search_requests sr
                    ON sr.search_request_id =
                       o.source_search_request_id

                LEFT JOIN applications a
                    ON a.opportunity_id =
                       o.opportunity_id

                LEFT JOIN opportunity_stage_history osh
                    ON osh.opportunity_id =
                       o.opportunity_id

                LEFT JOIN LATERAL (
                    SELECT
                        oe.event_type AS next_event_type,
                        oe.event_at AS next_event_at,
                        oe.notes AS next_event_notes
                    FROM opportunity_events oe
                    WHERE
                        oe.opportunity_id = o.opportunity_id
                        AND oe.event_type IN (
                            'deadline',
                            'follow_up',
                            'oa',
                            'interview'
                        )
                        AND oe.event_at >= NOW()
                    ORDER BY
                        oe.event_at ASC,
                        oe.event_id ASC
                    LIMIT 1
                ) next_event
                    ON TRUE

                WHERE
                    o.opportunity_id = :opportunity_id
                    AND o.profile_id = :profile_id;
                """
            ),
            {
                "opportunity_id": opportunity_id,
                "profile_id": profile_id,
            },
        )
        .mappings()
        .one_or_none()
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found.",
        )

    return dict(row)


def percentage(
    numerator: int,
    denominator: int,
):
    if denominator == 0:
        return 0.0

    return round(
        (numerator / denominator) * 100,
        1,
    )


@router.get("")
def list_opportunities(
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    with engine.connect() as connection:
        rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        o.opportunity_id,
                        o.profile_id,
                        o.job_id,
                        o.source_search_request_id,
                        o.current_status,
                        o.priority,
                        o.notes,
                        o.created_at,
                        o.updated_at,

                        j.raw_title,
                        j.raw_company_name,
                        j.location_raw,
                        j.job_url,
                        j.source,
                        j.date_posted,
                        j.derived_posted_date,

                        sr.query_text AS search_query,

                        a.application_id,
                        a.resume_id,
                        a.application_url,
                        a.application_method,
                        a.submitted_at,
                        a.referral_used,
                        a.cover_letter_used,
                        a.notes AS application_notes,

                        osh.tracked_at,
                        osh.applied_at,
                        osh.first_oa_at,
                        osh.first_interview_at,
                        osh.first_offer_at,
                        osh.first_rejection_at,
                        osh.first_withdrawal_at,
                        osh.first_response_at,

                        next_event.next_event_type,
                        next_event.next_event_at,
                        next_event.next_event_notes

                    FROM opportunities o

                    JOIN jobs j
                        ON j.job_id = o.job_id

                    LEFT JOIN search_requests sr
                        ON sr.search_request_id =
                           o.source_search_request_id

                    LEFT JOIN applications a
                        ON a.opportunity_id =
                           o.opportunity_id

                    LEFT JOIN opportunity_stage_history osh
                        ON osh.opportunity_id =
                           o.opportunity_id

                    LEFT JOIN LATERAL (
                        SELECT
                            oe.event_type AS next_event_type,
                            oe.event_at AS next_event_at,
                            oe.notes AS next_event_notes
                        FROM opportunity_events oe
                        WHERE
                            oe.opportunity_id = o.opportunity_id
                            AND oe.event_type IN (
                                'deadline',
                                'follow_up',
                                'oa',
                                'interview'
                            )
                            AND oe.event_at >= NOW()
                        ORDER BY
                            oe.event_at ASC,
                            oe.event_id ASC
                        LIMIT 1
                    ) next_event
                        ON TRUE

                    WHERE
                        o.profile_id = :profile_id

                    ORDER BY
                        o.updated_at DESC,
                        o.opportunity_id DESC;
                    """
                ),
                {
                    "profile_id": profile.profile_id,
                },
            )
            .mappings()
            .all()
        )

    return {
        "count": len(rows),
        "opportunities": [
            dict(row)
            for row in rows
        ],
    }


@router.post("")
def save_opportunity(
    request: CreateOpportunityRequest,
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    with engine.begin() as connection:
        job_exists = connection.execute(
            text(
                """
                SELECT 1
                FROM jobs
                WHERE job_id = :job_id
                LIMIT 1;
                """
            ),
            {
                "job_id": request.job_id,
            },
        ).scalar_one_or_none()

        if job_exists is None:
            raise HTTPException(
                status_code=404,
                detail="Job not found.",
            )

        if request.source_search_request_id is not None:
            search_job = connection.execute(
                text(
                    """
                    SELECT 1

                    FROM user_search_requests usr

                    JOIN job_relevance_scores jrs
                        ON jrs.search_request_id =
                           usr.search_request_id

                    WHERE
                        usr.profile_id = :profile_id
                        AND usr.search_request_id =
                            :search_request_id
                        AND jrs.job_id = :job_id

                    LIMIT 1;
                    """
                ),
                {
                    "profile_id": profile.profile_id,
                    "search_request_id":
                        request.source_search_request_id,
                    "job_id": request.job_id,
                },
            ).scalar_one_or_none()

            if search_job is None:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Job was not found "
                        "in that search."
                    ),
                )

        existing = (
            connection.execute(
                text(
                    """
                    SELECT opportunity_id
                    FROM opportunities
                    WHERE
                        profile_id = :profile_id
                        AND job_id = :job_id;
                    """
                ),
                {
                    "profile_id": profile.profile_id,
                    "job_id": request.job_id,
                },
            )
            .mappings()
            .one_or_none()
        )

        if existing is not None:
            opportunity_id = existing[
                "opportunity_id"
            ]

            connection.execute(
                text(
                    """
                    UPDATE opportunities
                    SET
                        priority = :priority,
                        notes = COALESCE(
                            :notes,
                            notes
                        ),
                        updated_at = NOW()
                    WHERE
                        opportunity_id =
                            :opportunity_id
                        AND profile_id =
                            :profile_id;
                    """
                ),
                {
                    "priority": request.priority,
                    "notes": request.notes,
                    "opportunity_id":
                        opportunity_id,
                    "profile_id":
                        profile.profile_id,
                },
            )

            return {
                "created": False,
                "opportunity":
                    fetch_opportunity_detail(
                        connection,
                        opportunity_id,
                        profile.profile_id,
                    ),
            }

        opportunity_id = connection.execute(
            text(
                """
                INSERT INTO opportunities (
                    profile_id,
                    job_id,
                    source_search_request_id,
                    current_status,
                    priority,
                    notes
                )
                VALUES (
                    :profile_id,
                    :job_id,
                    :search_request_id,
                    'saved',
                    :priority,
                    :notes
                )
                RETURNING opportunity_id;
                """
            ),
            {
                "profile_id": profile.profile_id,
                "job_id": request.job_id,
                "search_request_id":
                    request.source_search_request_id,
                "priority": request.priority,
                "notes": request.notes,
            },
        ).scalar_one()

        connection.execute(
            text(
                """
                INSERT INTO opportunity_events (
                    opportunity_id,
                    event_type,
                    from_status,
                    to_status,
                    event_source
                )
                VALUES (
                    :opportunity_id,
                    'created',
                    NULL,
                    'saved',
                    'manual'
                );
                """
            ),
            {
                "opportunity_id":
                    opportunity_id,
            },
        )

        return {
            "created": True,
            "opportunity":
                fetch_opportunity_detail(
                    connection,
                    opportunity_id,
                    profile.profile_id,
                ),
        }


@router.get("/analytics")
def get_opportunity_analytics(
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    with engine.connect() as connection:
        summary = (
            connection.execute(
                text(
                    """
                    SELECT
                        COUNT(*) AS tracked,

                        COUNT(*) FILTER (
                            WHERE ever_applied
                        ) AS applied,

                        COUNT(*) FILTER (
                            WHERE ever_oa
                        ) AS oa,

                        COUNT(*) FILTER (
                            WHERE ever_interview
                        ) AS interview,

                        COUNT(*) FILTER (
                            WHERE ever_offer
                        ) AS offer,

                        COUNT(*) FILTER (
                            WHERE ever_rejected
                        ) AS rejected,

                        COUNT(*) FILTER (
                            WHERE ever_withdrawn
                        ) AS withdrawn,

                        COUNT(*) FILTER (
                            WHERE first_response_at
                                  IS NOT NULL
                        ) AS responded,

                        AVG(
                            days_to_first_response
                        ) FILTER (
                            WHERE days_to_first_response
                                  IS NOT NULL
                        ) AS avg_days_to_response,

                        AVG(
                            days_to_interview
                        ) FILTER (
                            WHERE days_to_interview
                                  IS NOT NULL
                        ) AS avg_days_to_interview,

                        AVG(
                            days_to_offer
                        ) FILTER (
                            WHERE days_to_offer
                                  IS NOT NULL
                        ) AS avg_days_to_offer

                    FROM opportunity_analytics

                    WHERE
                        profile_id = :profile_id;
                    """
                ),
                {
                    "profile_id":
                        profile.profile_id,
                },
            )
            .mappings()
            .one()
        )

        status_rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        current_status,
                        COUNT(*) AS count

                    FROM opportunities

                    WHERE
                        profile_id = :profile_id

                    GROUP BY current_status

                    ORDER BY current_status;
                    """
                ),
                {
                    "profile_id":
                        profile.profile_id,
                },
            )
            .mappings()
            .all()
        )

        priority_rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        priority,
                        COUNT(*) AS count

                    FROM opportunities

                    WHERE
                        profile_id = :profile_id

                    GROUP BY priority

                    ORDER BY priority;
                    """
                ),
                {
                    "profile_id":
                        profile.profile_id,
                },
            )
            .mappings()
            .all()
        )

    tracked = int(
        summary["tracked"] or 0
    )
    applied = int(
        summary["applied"] or 0
    )
    oa = int(
        summary["oa"] or 0
    )
    interview = int(
        summary["interview"] or 0
    )
    offer = int(
        summary["offer"] or 0
    )
    responded = int(
        summary["responded"] or 0
    )

    def numeric_or_none(value):
        if value is None:
            return None
        return round(
            float(value),
            2,
        )

    return {
        "tracked_opportunities":
            tracked,

        "funnel": {
            "applied": applied,
            "oa": oa,
            "interview": interview,
            "offer": offer,
            "rejected": int(
                summary["rejected"] or 0
            ),
            "withdrawn": int(
                summary["withdrawn"] or 0
            ),
            "responded": responded,
        },

        "rates": {
            "application_rate_pct":
                percentage(
                    applied,
                    tracked,
                ),
            "response_rate_pct":
                percentage(
                    responded,
                    applied,
                ),
            "oa_rate_pct":
                percentage(
                    oa,
                    applied,
                ),
            "interview_rate_pct":
                percentage(
                    interview,
                    applied,
                ),
            "offer_rate_pct":
                percentage(
                    offer,
                    applied,
                ),
        },

        "timing": {
            "avg_days_to_response":
                numeric_or_none(
                    summary[
                        "avg_days_to_response"
                    ]
                ),
            "avg_days_to_interview":
                numeric_or_none(
                    summary[
                        "avg_days_to_interview"
                    ]
                ),
            "avg_days_to_offer":
                numeric_or_none(
                    summary[
                        "avg_days_to_offer"
                    ]
                ),
        },

        "by_status": [
            dict(row)
            for row in status_rows
        ],

        "by_priority": [
            dict(row)
            for row in priority_rows
        ],
    }


@router.post("/{opportunity_id}/events")
def create_opportunity_event(
    opportunity_id: int,
    request: CreateOpportunityEventRequest,
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    with engine.begin() as connection:
        get_owned_opportunity(
            connection,
            opportunity_id,
            profile.profile_id,
        )

        event_id = connection.execute(
            text(
                """
                INSERT INTO opportunity_events (
                    opportunity_id,
                    event_type,
                    event_at,
                    notes,
                    event_source
                )
                VALUES (
                    :opportunity_id,
                    :event_type,
                    COALESCE(:event_at, NOW()),
                    :notes,
                    'manual'
                )
                RETURNING event_id;
                """
            ),
            {
                "opportunity_id":
                    opportunity_id,
                "event_type":
                    request.event_type,
                "event_at":
                    request.event_at,
                "notes":
                    request.notes,
            },
        ).scalar_one()

        event = (
            connection.execute(
                text(
                    """
                    SELECT
                        event_id,
                        event_type,
                        from_status,
                        to_status,
                        event_at,
                        notes,
                        metadata,
                        event_source,
                        created_at
                    FROM opportunity_events
                    WHERE event_id = :event_id;
                    """
                ),
                {
                    "event_id":
                        event_id,
                },
            )
            .mappings()
            .one()
        )

    return {
        "created": True,
        "event":
            dict(event),
    }


@router.post("/{opportunity_id}/resume-comparison")
def compare_opportunity_resume(
    opportunity_id: int,
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    with engine.connect() as connection:
        opportunity = get_owned_opportunity(
            connection,
            opportunity_id,
            profile.profile_id,
        )

    try:
        return assess_job_fit(
            profile_id=
                profile.profile_id,

            job_id=
                opportunity[
                    "job_id"
                ],

            database_url=
                DATABASE_URL,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "CareerCompass could not "
                "compare this role with "
                "your current profile."
            ),
        ) from exc


@router.get("/{opportunity_id}")
def get_opportunity(
    opportunity_id: int,
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    with engine.connect() as connection:
        opportunity = (
            fetch_opportunity_detail(
                connection,
                opportunity_id,
                profile.profile_id,
            )
        )

        events = (
            connection.execute(
                text(
                    """
                    SELECT
                        event_id,
                        event_type,
                        from_status,
                        to_status,
                        event_at,
                        notes,
                        metadata,
                        event_source,
                        created_at

                    FROM opportunity_events

                    WHERE
                        opportunity_id =
                            :opportunity_id

                    ORDER BY
                        event_at ASC,
                        event_id ASC;
                    """
                ),
                {
                    "opportunity_id":
                        opportunity_id,
                },
            )
            .mappings()
            .all()
        )

    return {
        "opportunity":
            opportunity,
        "events": [
            dict(event)
            for event in events
        ],
    }


@router.delete("/{opportunity_id}")
def delete_opportunity(
    opportunity_id: int,
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    with engine.begin() as connection:
        opportunity = get_owned_opportunity(
            connection,
            opportunity_id,
            profile.profile_id,
        )

        connection.execute(
            text(
                """
                DELETE FROM applications
                WHERE
                    opportunity_id =
                        :opportunity_id;
                """
            ),
            {
                "opportunity_id":
                    opportunity_id,
            },
        )

        connection.execute(
            text(
                """
                DELETE FROM opportunity_events
                WHERE
                    opportunity_id =
                        :opportunity_id;
                """
            ),
            {
                "opportunity_id":
                    opportunity_id,
            },
        )

        connection.execute(
            text(
                """
                DELETE FROM opportunities
                WHERE
                    opportunity_id =
                        :opportunity_id
                    AND profile_id =
                        :profile_id;
                """
            ),
            {
                "opportunity_id":
                    opportunity_id,
                "profile_id":
                    profile.profile_id,
            },
        )

    return {
        "deleted": True,
        "opportunity_id":
            opportunity_id,
        "job_id":
            opportunity["job_id"],
    }


@router.patch("/{opportunity_id}")
def update_opportunity(
    opportunity_id: int,
    request: UpdateOpportunityRequest,
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    updates = request.model_dump(
        exclude_unset=True
    )

    with engine.begin() as connection:
        get_owned_opportunity(
            connection,
            opportunity_id,
            profile.profile_id,
        )

        if not updates:
            return {
                "updated": False,
                "opportunity":
                    fetch_opportunity_detail(
                        connection,
                        opportunity_id,
                        profile.profile_id,
                    ),
            }

        update_priority = (
            "priority" in updates
        )
        update_notes = (
            "notes" in updates
        )

        connection.execute(
            text(
                """
                UPDATE opportunities
                SET
                    priority =
                        CASE
                            WHEN :update_priority
                            THEN :priority
                            ELSE priority
                        END,

                    notes =
                        CASE
                            WHEN :update_notes
                            THEN :notes
                            ELSE notes
                        END,

                    updated_at = NOW()

                WHERE
                    opportunity_id =
                        :opportunity_id
                    AND profile_id =
                        :profile_id;
                """
            ),
            {
                "update_priority":
                    update_priority,
                "priority":
                    request.priority,
                "update_notes":
                    update_notes,
                "notes":
                    request.notes,
                "opportunity_id":
                    opportunity_id,
                "profile_id":
                    profile.profile_id,
            },
        )

        return {
            "updated": True,
            "opportunity":
                fetch_opportunity_detail(
                    connection,
                    opportunity_id,
                    profile.profile_id,
                ),
        }


@router.post("/{opportunity_id}/status")
def update_opportunity_status(
    opportunity_id: int,
    request: UpdateStatusRequest,
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    with engine.begin() as connection:
        opportunity = get_owned_opportunity(
            connection,
            opportunity_id,
            profile.profile_id,
        )

        old_status = opportunity[
            "current_status"
        ]

        if old_status == request.status:
            return {
                "changed": False,
                "from_status":
                    old_status,
                "to_status":
                    request.status,
                "opportunity":
                    fetch_opportunity_detail(
                        connection,
                        opportunity_id,
                        profile.profile_id,
                    ),
            }

        connection.execute(
            text(
                """
                UPDATE opportunities
                SET
                    current_status =
                        :new_status,
                    updated_at = NOW()
                WHERE
                    opportunity_id =
                        :opportunity_id
                    AND profile_id =
                        :profile_id;
                """
            ),
            {
                "new_status":
                    request.status,
                "opportunity_id":
                    opportunity_id,
                "profile_id":
                    profile.profile_id,
            },
        )

        connection.execute(
            text(
                """
                INSERT INTO opportunity_events (
                    opportunity_id,
                    event_type,
                    from_status,
                    to_status,
                    notes,
                    event_source
                )
                VALUES (
                    :opportunity_id,
                    'status_change',
                    :old_status,
                    :new_status,
                    :notes,
                    'manual'
                );
                """
            ),
            {
                "opportunity_id":
                    opportunity_id,
                "old_status":
                    old_status,
                "new_status":
                    request.status,
                "notes":
                    request.notes,
            },
        )

        return {
            "changed": True,
            "from_status":
                old_status,
            "to_status":
                request.status,
            "opportunity":
                fetch_opportunity_detail(
                    connection,
                    opportunity_id,
                    profile.profile_id,
                ),
        }


@router.post("/{opportunity_id}/application")
def record_application(
    opportunity_id: int,
    request: RecordApplicationRequest,
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    with engine.begin() as connection:
        opportunity = get_owned_opportunity(
            connection,
            opportunity_id,
            profile.profile_id,
        )

        if request.resume_id is not None:
            resume_owned = (
                connection.execute(
                    text(
                        """
                        SELECT 1

                        FROM resume_documents

                        WHERE
                            resume_id = :resume_id
                            AND profile_id =
                                :profile_id

                        LIMIT 1;
                        """
                    ),
                    {
                        "resume_id":
                            request.resume_id,
                        "profile_id":
                            profile.profile_id,
                    },
                )
                .scalar_one_or_none()
            )

            if resume_owned is None:
                raise HTTPException(
                    status_code=404,
                    detail="Resume not found.",
                )

        previous_status = opportunity[
            "current_status"
        ]

        application_id = connection.execute(
            text(
                """
                INSERT INTO applications (
                    opportunity_id,
                    resume_id,
                    application_url,
                    application_method,
                    referral_used,
                    cover_letter_used,
                    notes
                )
                VALUES (
                    :opportunity_id,
                    :resume_id,
                    :application_url,
                    :application_method,
                    :referral_used,
                    :cover_letter_used,
                    :notes
                )

                ON CONFLICT (opportunity_id)

                DO UPDATE SET
                    resume_id =
                        EXCLUDED.resume_id,
                    application_url =
                        EXCLUDED.application_url,
                    application_method =
                        EXCLUDED.application_method,
                    referral_used =
                        EXCLUDED.referral_used,
                    cover_letter_used =
                        EXCLUDED.cover_letter_used,
                    notes =
                        EXCLUDED.notes,
                    updated_at = NOW()

                RETURNING application_id;
                """
            ),
            {
                "opportunity_id":
                    opportunity_id,
                "resume_id":
                    request.resume_id,
                "application_url":
                    request.application_url,
                "application_method":
                    request.application_method,
                "referral_used":
                    request.referral_used,
                "cover_letter_used":
                    request.cover_letter_used,
                "notes":
                    request.notes,
            },
        ).scalar_one()

        status_changed = False

        if (
            previous_status
            in EARLY_APPLICATION_STATUSES
        ):
            connection.execute(
                text(
                    """
                    UPDATE opportunities
                    SET
                        current_status =
                            'applied',
                        updated_at = NOW()
                    WHERE
                        opportunity_id =
                            :opportunity_id
                        AND profile_id =
                            :profile_id;
                    """
                ),
                {
                    "opportunity_id":
                        opportunity_id,
                    "profile_id":
                        profile.profile_id,
                },
            )

            connection.execute(
                text(
                    """
                    INSERT INTO opportunity_events (
                        opportunity_id,
                        event_type,
                        from_status,
                        to_status,
                        notes,
                        event_source
                    )
                    VALUES (
                        :opportunity_id,
                        'status_change',
                        :from_status,
                        'applied',
                        'Application recorded',
                        'manual'
                    );
                    """
                ),
                {
                    "opportunity_id":
                        opportunity_id,
                    "from_status":
                        previous_status,
                },
            )

            status_changed = True

        return {
            "application_id":
                application_id,
            "status_changed":
                status_changed,
            "opportunity":
                fetch_opportunity_detail(
                    connection,
                    opportunity_id,
                    profile.profile_id,
                ),
        }
