import os
from uuid import UUID

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from api.auth import (
    AuthenticatedUser,
    get_current_user,
)
from src.collection.database import (
    create_database_engine,
)


load_dotenv()


database_url = os.getenv(
    "SUPABASE_DATABASE_URL"
)

engine = create_database_engine(
    database_url
)


class CurrentProfile(BaseModel):
    profile_id: int
    user_id: UUID
    profile_name: str


def get_current_profile(
    user: AuthenticatedUser = Depends(
        get_current_user
    ),
) -> CurrentProfile:

    with engine.connect() as connection:

        profile = connection.execute(
            text(
                """
                SELECT
                    profile_id,
                    user_id,
                    profile_name
                FROM public.user_profiles
                WHERE user_id = :user_id
                """
            ),
            {
                "user_id": str(user.id),
            },
        ).mappings().one_or_none()

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="CareerCompass profile not found",
        )

    return CurrentProfile(
        profile_id=profile["profile_id"],
        user_id=profile["user_id"],
        profile_name=profile["profile_name"],
    )