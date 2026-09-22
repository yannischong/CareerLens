from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)
from src.services.job_fit_service import (
    assess_job_fit,
)


def assess_manual_job_fit(
    profile_id,
    job_id,
    database_url=None,
):
    engine = create_database_engine(
        database_url
    )


    with engine.connect() as connection:

        owned = (
            connection.execute(
                text(
                    """
                    SELECT 1

                    FROM
                        manual_job_imports

                    WHERE
                        profile_id =
                            :profile_id

                        AND
                        job_id =
                            :job_id

                    LIMIT 1;
                    """
                ),
                {
                    "profile_id":
                        profile_id,

                    "job_id":
                        job_id,
                },
            )
            .scalar_one_or_none()
        )


    if owned is None:

        raise ValueError(
            "Imported job not found."
        )


    return assess_job_fit(
        profile_id=
            profile_id,

        job_id=
            job_id,

        database_url=
            database_url,
    )
