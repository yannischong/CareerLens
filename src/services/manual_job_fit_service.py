from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)
from src.services.job_fit_service import (
    assess_job_fit,
)
from src.user_profile.map_profile_concepts import (
    map_profile_concepts,
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


    # New manual jobs can introduce
    # concepts that did not exist when
    # the resume was originally mapped.
    # Rebuild the profile mapping first
    # so the comparison uses the same
    # active concept vocabulary.
    map_profile_concepts(
        profile_id=
            profile_id,

        database_url=
            database_url,
    )


    return assess_job_fit(
        profile_id=
            profile_id,

        job_id=
            job_id,

        database_url=
            database_url,
    )
