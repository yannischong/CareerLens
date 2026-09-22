from sqlalchemy import text

from src.collection.database import create_database_engine


SEARCH_LIMIT = 2


def get_search_quota(
    profile_id,
    database_url=None,
):
    engine = create_database_engine(database_url)

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT searches_used
                FROM user_search_quota
                WHERE profile_id = :profile_id
                """
            ),
            {
                "profile_id": profile_id,
            },
        ).mappings().one_or_none()

    searches_used = (
        row["searches_used"]
        if row
        else 0
    )

    return {
        "limit": SEARCH_LIMIT,
        "used": searches_used,
        "remaining": max(
            SEARCH_LIMIT - searches_used,
            0,
        ),
    }


def reserve_search_slot(
    profile_id,
    database_url=None,
):
    engine = create_database_engine(database_url)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO user_search_quota (
                    profile_id,
                    searches_used
                )
                VALUES (
                    :profile_id,
                    0
                )
                ON CONFLICT (profile_id)
                DO NOTHING
                """
            ),
            {
                "profile_id": profile_id,
            },
        )

        row = connection.execute(
            text(
                """
                UPDATE user_search_quota
                SET
                    searches_used = searches_used + 1,
                    last_search_at = NOW(),
                    updated_at = NOW()
                WHERE
                    profile_id = :profile_id
                    AND searches_used < :limit
                RETURNING searches_used
                """
            ),
            {
                "profile_id": profile_id,
                "limit": SEARCH_LIMIT,
            },
        ).mappings().one_or_none()

    if row is None:
        return {
            "allowed": False,
            "limit": SEARCH_LIMIT,
            "used": SEARCH_LIMIT,
            "remaining": 0,
        }

    searches_used = row["searches_used"]

    return {
        "allowed": True,
        "limit": SEARCH_LIMIT,
        "used": searches_used,
        "remaining": (
            SEARCH_LIMIT - searches_used
        ),
    }