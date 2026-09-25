import json
import os

from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel
from sqlalchemy import text

from api.profile import (
    CurrentProfile,
    get_current_profile,
)
from src.collection.database import (
    create_database_engine,
)
from src.extraction.model_skill_extractor import (
    enrich_manual_requirement_mentions,
)
from src.extraction.rules import (
    extract_requirements,
)
from src.services.manual_job_fit_service import (
    assess_manual_job_fit,
)
from src.services.manual_job_import_service import (
    get_manual_job,
    import_manual_job,
    list_manual_jobs,
)
from src.services.manual_job_service import (
    JobPageFetchError,
    fetch_job_listing,
)
from src.taxonomy.skill_classifier import (
    find_hard_skills,
    find_soft_skills,
)


load_dotenv()


router = APIRouter(
    prefix="/api/manual-jobs",
    tags=["Manual Jobs"],
)


DATABASE_URL = os.getenv(
    "SUPABASE_DATABASE_URL"
)


engine = create_database_engine(
    DATABASE_URL
)


ANALYSIS_VERSION = (
    "manual_analysis_snapshot_v1"
)


class ManualJobPreviewRequest(
    BaseModel
):
    url: str
    description_override: str | None = None


class ManualJobImportRequest(
    ManualJobPreviewRequest
):
    preview: dict | None = None


def _serialize_requirement(
    mention,
):
    metadata = dict(
        mention.structured_value
        or {}
    )

    concepts = []
    seen = set()

    for item in (
        metadata.get(
            "model_skills"
        )
        or []
    ):
        if not isinstance(
            item,
            dict,
        ):
            continue

        name = str(
            item.get(
                "canonical_name",
                "",
            )
        ).strip()

        concept_type = item.get(
            "skill_type"
        )

        if (
            not name
            or concept_type
            not in {
                "hard_skill",
                "soft_skill",
            }
        ):
            continue

        key = (
            concept_type,
            name.casefold(),
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        try:
            confidence = float(
                item.get(
                    "confidence"
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            confidence = None

        concepts.append(
            {
                "name": name,
                "type": concept_type,
                "confidence": confidence,
            }
        )

    # Rule-based fallback for listings where model extraction is disabled or
    # unavailable. These helpers are deliberately conservative.
    if not concepts:
        for candidate in (
            find_hard_skills(
                mention.raw_text
            )
            + find_soft_skills(
                mention.raw_text
            )
        ):
            name = str(
                candidate.get(
                    "raw_text",
                    "",
                )
            ).strip()

            concept_type = candidate.get(
                "concept_type"
            )

            if (
                not name
                or concept_type
                not in {
                    "hard_skill",
                    "soft_skill",
                }
            ):
                continue

            key = (
                concept_type,
                name.casefold(),
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            confidence = candidate.get(
                "confidence"
            )

            concepts.append(
                {
                    "name": name,
                    "type": concept_type,
                    "confidence": confidence,
                }
            )

    return {
        "requirement_type":
            mention.requirement_type,

        "requirement_level":
            mention.requirement_level,

        "text":
            mention.raw_text,

        "normalized_text":
            mention.normalized_text,

        "structured_value":
            metadata,

        "concepts":
            concepts,
    }


def _fallback_listing(
    url,
    description,
):
    description = description.strip()

    return {
        "url": url,
        "title": "Job listing",
        "company": None,
        "location": None,
        "employment_type": None,
        "date_posted": None,
        "description": description,
        "description_characters": len(
            description
        ),
        "extraction_method": "manual_description",
        "needs_description": False,
    }


def _resolve_listing(
    request,
    *,
    enrich_skills,
):
    url = request.url.strip()

    if not url:
        raise HTTPException(
            status_code=400,
            detail=(
                "Paste a job listing URL first."
            ),
        )

    manual_description = (
        request.description_override
        or ""
    ).strip()

    try:
        result = fetch_job_listing(
            url
        )

    except JobPageFetchError as exc:
        if manual_description:
            result = _fallback_listing(
                url,
                manual_description,
            )
        else:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": str(
                        exc
                    ),
                    "needs_description": True,
                },
            ) from exc

    if manual_description:
        result[
            "description"
        ] = manual_description

        result[
            "description_characters"
        ] = len(
            manual_description
        )

        result[
            "extraction_method"
        ] = "manual_description"

        result[
            "needs_description"
        ] = False

    description = (
        result.get(
            "description"
        )
        or ""
    ).strip()

    mentions = (
        extract_requirements(
            description
        )
        if description
        else []
    )

    if (
        description
        and enrich_skills
    ):
        mentions = (
            enrich_manual_requirement_mentions(
                description,
                mentions,
            )
        )

    requirements = [
        _serialize_requirement(
            mention
        )
        for mention in mentions
    ]

    result[
        "requirements"
    ] = requirements

    result[
        "requirement_count"
    ] = len(
        requirements
    )

    return result


def _latest_resume(
    profile_id,
):
    with engine.connect() as connection:
        return (
            connection.execute(
                text(
                    """
                    SELECT
                        resume_id,
                        original_filename
                    FROM resume_documents
                    WHERE profile_id = :profile_id
                    ORDER BY resume_id DESC
                    LIMIT 1;
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


def _verify_manual_job(
    profile_id,
    job_id,
):
    with engine.connect() as connection:
        owned = connection.execute(
            text(
                """
                SELECT 1
                FROM manual_job_imports
                WHERE
                    profile_id = :profile_id
                    AND job_id = :job_id
                LIMIT 1;
                """
            ),
            {
                "profile_id": profile_id,
                "job_id": job_id,
            },
        ).scalar_one_or_none()

    if owned is None:
        raise HTTPException(
            status_code=404,
            detail="Imported job not found.",
        )


def _save_listing_snapshot(
    profile_id,
    job_id,
    listing,
):
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO manual_job_analysis_snapshots (
                    profile_id,
                    job_id,
                    listing_snapshot,
                    resume_fit_snapshot,
                    resume_id,
                    analysis_version,
                    updated_at
                )
                VALUES (
                    :profile_id,
                    :job_id,
                    CAST(:listing_snapshot AS JSONB),
                    NULL,
                    NULL,
                    :analysis_version,
                    NOW()
                )
                ON CONFLICT (profile_id, job_id)
                DO UPDATE SET
                    listing_snapshot =
                        EXCLUDED.listing_snapshot,
                    resume_fit_snapshot = NULL,
                    resume_id = NULL,
                    analysis_version =
                        EXCLUDED.analysis_version,
                    updated_at = NOW();
                """
            ),
            {
                "profile_id": profile_id,
                "job_id": job_id,
                "listing_snapshot": json.dumps(
                    listing,
                    default=str,
                ),
                "analysis_version":
                    ANALYSIS_VERSION,
            },
        )


def _save_resume_snapshot(
    profile_id,
    job_id,
    resume_id,
    analysis,
):
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO manual_job_analysis_snapshots (
                    profile_id,
                    job_id,
                    listing_snapshot,
                    resume_fit_snapshot,
                    resume_id,
                    analysis_version,
                    updated_at
                )
                VALUES (
                    :profile_id,
                    :job_id,
                    '{}'::JSONB,
                    CAST(:resume_fit_snapshot AS JSONB),
                    :resume_id,
                    :analysis_version,
                    NOW()
                )
                ON CONFLICT (profile_id, job_id)
                DO UPDATE SET
                    resume_fit_snapshot =
                        EXCLUDED.resume_fit_snapshot,
                    resume_id =
                        EXCLUDED.resume_id,
                    analysis_version =
                        EXCLUDED.analysis_version,
                    updated_at = NOW();
                """
            ),
            {
                "profile_id": profile_id,
                "job_id": job_id,
                "resume_fit_snapshot":
                    json.dumps(
                        analysis,
                        default=str,
                    ),
                "resume_id": resume_id,
                "analysis_version":
                    ANALYSIS_VERSION,
            },
        )


def _load_snapshot(
    profile_id,
    job_id,
):
    with engine.connect() as connection:
        return (
            connection.execute(
                text(
                    """
                    SELECT
                        s.listing_snapshot,
                        s.resume_fit_snapshot,
                        s.resume_id,
                        s.analysis_version,
                        s.updated_at,
                        r.original_filename
                            AS resume_filename
                    FROM manual_job_analysis_snapshots s
                    LEFT JOIN resume_documents r
                        ON r.resume_id = s.resume_id
                    WHERE
                        s.profile_id = :profile_id
                        AND s.job_id = :job_id;
                    """
                ),
                {
                    "profile_id": profile_id,
                    "job_id": job_id,
                },
            )
            .mappings()
            .one_or_none()
        )


@router.post("/preview")
def preview_manual_job(
    request: ManualJobPreviewRequest,
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    del profile

    return _resolve_listing(
        request,
        enrich_skills=True,
    )


@router.post("/import")
def import_manual_listing(
    request: ManualJobImportRequest,
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    if isinstance(
        request.preview,
        dict,
    ):
        listing = dict(
            request.preview
        )

        listing[
            "url"
        ] = request.url.strip()

        if (
            request.description_override
            and request.description_override.strip()
        ):
            description = (
                request.description_override.strip()
            )

            listing[
                "description"
            ] = description

            listing[
                "description_characters"
            ] = len(
                description
            )

            listing[
                "extraction_method"
            ] = "manual_description"

            listing[
                "needs_description"
            ] = False
    else:
        listing = _resolve_listing(
            request,
            enrich_skills=True,
        )

    try:
        result = import_manual_job(
            profile_id=
                profile.profile_id,
            listing=listing,
            database_url=DATABASE_URL,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        ) from exc

    job_id = result[
        "job"
    ][
        "job_id"
    ]

    _save_listing_snapshot(
        profile.profile_id,
        job_id,
        listing,
    )

    # Adding a manual listing and tracking it are one user action.
    # Persist the opportunity here so a successful import can never be
    # followed by a browser-side failure that leaves My Applications empty.
    with engine.begin() as connection:
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
                    "job_id": job_id,
                },
            )
            .mappings()
            .one_or_none()
        )

        if existing is None:
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
                        NULL,
                        'saved',
                        'medium',
                        NULL
                    )
                    RETURNING opportunity_id;
                    """
                ),
                {
                    "profile_id": profile.profile_id,
                    "job_id": job_id,
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
                    "opportunity_id": opportunity_id,
                },
            )

            opportunity_created = True
        else:
            opportunity_id = existing[
                "opportunity_id"
            ]
            opportunity_created = False

    result[
        "opportunity_id"
    ] = opportunity_id
    result[
        "opportunity_created"
    ] = opportunity_created

    return result


@router.get("")
def manual_jobs(
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    jobs = list_manual_jobs(
        profile_id=
            profile.profile_id,
        database_url=DATABASE_URL,
    )

    return {
        "count": len(
            jobs
        ),
        "jobs": jobs,
    }


@router.get("/{job_id}")
def manual_job(
    job_id: int,
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    job = get_manual_job(
        profile_id=
            profile.profile_id,
        job_id=job_id,
        database_url=DATABASE_URL,
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Imported job not found.",
        )

    return job


@router.get("/{job_id}/snapshot")
def manual_job_snapshot(
    job_id: int,
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    _verify_manual_job(
        profile.profile_id,
        job_id,
    )

    snapshot = _load_snapshot(
        profile.profile_id,
        job_id,
    )

    latest = _latest_resume(
        profile.profile_id
    )

    if snapshot is None:
        return {
            "job_id": job_id,
            "listing_snapshot": None,
            "resume_fit_snapshot": None,
            "resume_id": None,
            "resume_filename": None,
            "latest_resume_id": (
                latest[
                    "resume_id"
                ]
                if latest
                else None
            ),
            "latest_resume_filename": (
                latest[
                    "original_filename"
                ]
                if latest
                else None
            ),
            "resume_fit_current": False,
            "analysis_version":
                ANALYSIS_VERSION,
        }

    saved_resume_id = snapshot[
        "resume_id"
    ]

    latest_resume_id = (
        latest[
            "resume_id"
        ]
        if latest
        else None
    )

    return {
        "job_id": job_id,
        "listing_snapshot": (
            snapshot[
                "listing_snapshot"
            ]
            or None
        ),
        "resume_fit_snapshot":
            snapshot[
                "resume_fit_snapshot"
            ],
        "resume_id":
            saved_resume_id,
        "resume_filename":
            snapshot[
                "resume_filename"
            ],
        "latest_resume_id":
            latest_resume_id,
        "latest_resume_filename": (
            latest[
                "original_filename"
            ]
            if latest
            else None
        ),
        "resume_fit_current": (
            snapshot[
                "resume_fit_snapshot"
            ]
            is not None
            and saved_resume_id
            is not None
            and saved_resume_id
            == latest_resume_id
        ),
        "analysis_version":
            snapshot[
                "analysis_version"
            ],
        "updated_at":
            snapshot[
                "updated_at"
            ],
    }


@router.post("/{job_id}/analyze")
def analyze_manual_job(
    job_id: int,
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    _verify_manual_job(
        profile.profile_id,
        job_id,
    )

    latest = _latest_resume(
        profile.profile_id
    )

    snapshot = _load_snapshot(
        profile.profile_id,
        job_id,
    )

    latest_resume_id = (
        latest[
            "resume_id"
        ]
        if latest
        else None
    )

    if (
        snapshot is not None
        and snapshot[
            "resume_fit_snapshot"
        ]
        is not None
        and snapshot[
            "resume_id"
        ]
        == latest_resume_id
    ):
        cached = dict(
            snapshot[
                "resume_fit_snapshot"
            ]
        )

        cached[
            "cached"
        ] = True

        cached[
            "resume_id"
        ] = latest_resume_id

        cached[
            "resume_filename"
        ] = (
            latest[
                "original_filename"
            ]
            if latest
            else None
        )

        return cached

    try:
        analysis = assess_manual_job_fit(
            profile_id=
                profile.profile_id,
            job_id=job_id,
            database_url=DATABASE_URL,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(
                exc
            ),
        ) from exc

    analysis[
        "cached"
    ] = False

    analysis[
        "resume_id"
    ] = latest_resume_id

    analysis[
        "resume_filename"
    ] = (
        latest[
            "original_filename"
        ]
        if latest
        else None
    )

    _save_resume_snapshot(
        profile.profile_id,
        job_id,
        latest_resume_id,
        analysis,
    )

    return analysis
