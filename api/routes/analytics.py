import os

from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy import text

from api.profile import (
    CurrentProfile,
    get_current_profile,
)
from src.analytics.skill_gap_priority import (
    build_gap_priority,
)
from src.collection.database import (
    create_database_engine,
)


load_dotenv()


router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"],
)


DATABASE_URL = os.getenv(
    "SUPABASE_DATABASE_URL"
)


engine = create_database_engine(
    DATABASE_URL
)


def verify_search_ownership(
    search_request_id: int,
    profile: CurrentProfile,
):
    with engine.connect() as connection:

        owned = connection.execute(
            text(
                """
                SELECT
                    1

                FROM
                    user_search_requests

                WHERE
                    profile_id =
                        :profile_id

                    AND
                    search_request_id =
                        :search_request_id

                LIMIT 1;
                """
            ),
            {
                "profile_id":
                    profile.profile_id,

                "search_request_id":
                    search_request_id,
            },
        ).scalar_one_or_none()


    if owned is None:

        raise HTTPException(
            status_code=404,
            detail="Search not found.",
        )


def get_latest_search_request_id(
    profile: CurrentProfile,
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
            detail="No job search found.",
        )


    return latest_search[
        "search_request_id"
    ]


def build_skill_gap_response(
    search_request_id: int,
    profile: CurrentProfile,
):
    try:

        return build_gap_priority(
            profile_id=
                profile.profile_id,

            search_request_id=
                search_request_id,

            database_url=
                DATABASE_URL,
        )


    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.get(
    "/latest/skill-gaps"
)
def get_latest_skill_gap_intelligence(
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    search_request_id = (
        get_latest_search_request_id(
            profile
        )
    )


    return build_skill_gap_response(
        search_request_id=
            search_request_id,

        profile=
            profile,
    )


@router.get(
    "/skill-gaps/{search_request_id}"
)
def get_skill_gap_intelligence(
    search_request_id: int,

    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    verify_search_ownership(
        search_request_id=
            search_request_id,

        profile=
            profile,
    )


    return build_skill_gap_response(
        search_request_id=
            search_request_id,

        profile=
            profile,
    )