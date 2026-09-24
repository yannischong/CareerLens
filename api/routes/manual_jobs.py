import logging
import os

from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel

from api.profile import (
    CurrentProfile,
    get_current_profile,
)
from src.extraction.rules import (
    extract_requirements,
)
from src.extraction.model_skill_extractor import (
    enrich_manual_requirement_mentions,
)
from src.taxonomy.atomic import (
    extract_atomic_concepts,
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


load_dotenv()


logger = logging.getLogger(
    __name__
)


router = APIRouter(
    prefix="/api/manual-jobs",
    tags=["Manual Jobs"],
)


DATABASE_URL = os.getenv(
    "SUPABASE_DATABASE_URL"
)


class ManualJobRequest(
    BaseModel
):
    url: str
    description_override: (
        str
        | None
    ) = None


def serialize_requirement(
    mention,
):
    concepts = (
        extract_atomic_concepts(
            mention.raw_text,
            mention.requirement_type,
            structured_value=(
                mention.structured_value
                or {}
            ),
        )
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
            mention.structured_value,

        "concepts": [
            {
                "name":
                    concept[
                        "raw_text"
                    ],

                "type":
                    concept.get(
                        "concept_type",
                        mention
                        .requirement_type,
                    ),

                "confidence":
                    concept.get(
                        "confidence"
                    ),
            }

            for concept in concepts
        ],
    }


def prepare_listing(
    request:
        ManualJobRequest,
):
    url = request.url.strip()


    if not url:

        raise HTTPException(
            status_code=400,
            detail=(
                "Paste a job listing "
                "URL first."
            ),
        )


    manual_description = (
        request
        .description_override
        .strip()

        if (
            request
            .description_override
        )

        else ""
    )


    try:

        result = (
            fetch_job_listing(
                url
            )
        )


    except JobPageFetchError as exc:

        if manual_description:

            result = {
                "url":
                    url,

                "title":
                    "Job listing",

                "company":
                    None,

                "location":
                    None,

                "employment_type":
                    None,

                "date_posted":
                    None,

                "description":
                    manual_description,

                "description_characters":
                    len(
                        manual_description
                    ),

                "extraction_method":
                    "manual_description",

                "needs_description":
                    False,
            }


        else:

            raise HTTPException(
                status_code=422,

                detail={
                    "message":
                        str(
                            exc
                        ),

                    "needs_description":
                        True,
                },
            ) from exc


    if manual_description:

        result[
            "description"
        ] = (
            manual_description
        )


        result[
            "description_characters"
        ] = len(
            manual_description
        )


        result[
            "extraction_method"
        ] = (
            "manual_description"
        )


        result[
            "needs_description"
        ] = False


    description = (
        result.get(
            "description"
        )
        or ""
    )


    if description:
        mentions = extract_requirements(
            description,
            source_field="description",
        )

        mentions = enrich_manual_requirement_mentions(
            description,
            mentions,
            source_field="description",
        )

        requirements = [
            serialize_requirement(
                mention
            )
            for mention in mentions
        ]

    else:
        requirements = []


    result[
        "requirements"
    ] = requirements


    result[
        "requirement_count"
    ] = len(
        requirements
    )


    return result


@router.get("")
def manual_jobs(
    profile:
        CurrentProfile = Depends(
            get_current_profile
        ),
):

    jobs = list_manual_jobs(
        profile_id=
            profile.profile_id,

        database_url=
            DATABASE_URL,
    )


    return {
        "count":
            len(
                jobs
            ),

        "jobs":
            jobs,
    }


@router.post("/preview")
def preview_manual_job(
    request:
        ManualJobRequest,

    profile:
        CurrentProfile = Depends(
            get_current_profile
        ),
):

    del profile


    return prepare_listing(
        request
    )


@router.post("/import")
def import_manual_job_route(
    request:
        ManualJobRequest,

    profile:
        CurrentProfile = Depends(
            get_current_profile
        ),
):

    listing = prepare_listing(
        request
    )


    try:

        return import_manual_job(
            profile_id=
                profile.profile_id,

            listing=
                listing,

            database_url=
                DATABASE_URL,
        )


    except ValueError as exc:

        raise HTTPException(
            status_code=422,
            detail=str(
                exc
            ),
        ) from exc


    except Exception as exc:

        logger.exception(
            "Manual job import failed"
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "CareerCompass could not "
                "save this job listing."
            ),
        ) from exc


@router.get("/{job_id}")
def manual_job_detail(
    job_id: int,

    profile:
        CurrentProfile = Depends(
            get_current_profile
        ),
):

    job = get_manual_job(
        profile_id=
            profile.profile_id,

        job_id=
            job_id,

        database_url=
            DATABASE_URL,
    )


    if job is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Imported job not found."
            ),
        )


    return {
        "job":
            job,
    }

@router.post("/{job_id}/analyze")
def analyze_manual_job(
    job_id: int,

    profile:
        CurrentProfile = Depends(
            get_current_profile
        ),
):

    try:

        return assess_manual_job_fit(
            profile_id=
                profile.profile_id,

            job_id=
                job_id,

            database_url=
                DATABASE_URL,
        )


    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(
                exc
            ),
        ) from exc


    except Exception as exc:

        logger.exception(
            "Manual job profile fit "
            "analysis failed"
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "CareerCompass could not "
                "analyse this role against "
                "your current profile."
            ),
        ) from exc
