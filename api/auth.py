import os
from uuid import UUID

import requests
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from pydantic import BaseModel


load_dotenv()


security = HTTPBearer(
    auto_error=False,
)


class AuthenticatedUser(BaseModel):
    id: UUID
    email: str | None = None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
) -> AuthenticatedUser:

    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    supabase_url = os.getenv("SUPABASE_URL")
    publishable_key = os.getenv(
        "SUPABASE_PUBLISHABLE_KEY"
    )

    if not supabase_url or not publishable_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is not configured",
        )

    try:
        response = requests.get(
            f"{supabase_url.rstrip('/')}/auth/v1/user",
            headers={
                "apikey": publishable_key,
                "Authorization": (
                    f"Bearer {credentials.credentials}"
                ),
            },
            timeout=10,
        )

    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    user_data = response.json()

    user_id = user_data.get("id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated user",
        )

    try:
        user_uuid = UUID(user_id)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated user",
        )

    return AuthenticatedUser(
        id=user_uuid,
        email=user_data.get("email"),
    )