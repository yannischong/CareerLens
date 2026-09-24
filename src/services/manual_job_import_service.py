import hashlib
import json
from datetime import date

from sqlalchemy import text

from src.cleaning.normalization import (
    derive_posted_date,
    normalize_company_name,
    normalize_description,
    normalize_location,
    normalize_title,
)
from src.cleaning.quality import (
    build_quality_flags,
)
from src.collection.database import (
    create_database_engine,
    upsert_job,
)
from src.collection.models import (
    NormalizedJob,
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


MANUAL_SOURCE = "manual_url"

NORMALIZATION_VERSION = (
    "normalize_v1"
)

REQUIREMENT_VERSION = (
    "requirements_v2"
)

CONCEPT_VERSION = (
    "atomic_concepts_v2"
)


def _parse_date(
    value,
):
    if value is None:
        return None

    if isinstance(
        value,
        date,
    ):
        return value

    cleaned = str(
        value
    ).strip()

    if not cleaned:
        return None

    try:
        return date.fromisoformat(
            cleaned[:10]
        )

    except ValueError:
        return None


def _manual_source_job_id(
    profile_id,
    url,
):
    # Manual imports are deliberately
    # profile-specific.
    #
    # This prevents one user's manually
    # pasted description from overwriting
    # another user's copy of the same URL.
    value = (
        f"{profile_id}:"
        f"{url.strip()}"
    )

    return hashlib.sha256(
        value.encode(
            "utf-8"
        )
    ).hexdigest()


def _normalize_imported_job(
    connection,
    job_id,
):
    job = (
        connection.execute(
            text(
                """
                SELECT
                    job_id,
                    raw_title,
                    raw_company_name,
                    location_raw,
                    description,
                    date_posted,
                    first_seen_at,
                    source_metadata

                FROM jobs

                WHERE
                    job_id =
                        :job_id;
                """
            ),
            {
                "job_id":
                    job_id,
            },
        )
        .mappings()
        .one()
    )


    normalized_title = (
        normalize_title(
            job[
                "raw_title"
            ]
        )
    )


    normalized_company = (
        normalize_company_name(
            job[
                "raw_company_name"
            ]
        )
    )


    normalized_location = (
        normalize_location(
            job[
                "location_raw"
            ]
        )
    )


    normalized_description = (
        normalize_description(
            job[
                "description"
            ]
        )
    )


    derived_date, date_method = (
        derive_posted_date(
            job[
                "date_posted"
            ],

            job[
                "source_metadata"
            ],

            job[
                "first_seen_at"
            ],
        )
    )


    quality_flags = (
        build_quality_flags(
            job
        )
    )


    connection.execute(
        text(
            """
            UPDATE jobs

            SET
                normalized_title =
                    :normalized_title,

                normalized_company_name =
                    :normalized_company,

                normalized_location =
                    :normalized_location,

                normalized_description =
                    :normalized_description,

                derived_posted_date =
                    :derived_posted_date,

                derived_posted_date_method =
                    :date_method,

                normalization_version =
                    :normalization_version,

                normalized_at =
                    NOW()

            WHERE
                job_id =
                    :job_id;
            """
        ),
        {
            "normalized_title":
                normalized_title,

            "normalized_company":
                normalized_company,

            "normalized_location":
                normalized_location,

            "normalized_description":
                normalized_description,

            "derived_posted_date":
                derived_date,

            "date_method":
                date_method,

            "normalization_version":
                NORMALIZATION_VERSION,

            "job_id":
                job_id,
        },
    )


    connection.execute(
        text(
            """
            DELETE FROM
                job_quality_flags

            WHERE
                job_id =
                    :job_id

                AND
                generated_by =
                    :generated_by;
            """
        ),
        {
            "job_id":
                job_id,

            "generated_by":
                NORMALIZATION_VERSION,
        },
    )


    for (
        flag_code,
        details,
    ) in quality_flags:

        connection.execute(
            text(
                """
                INSERT INTO
                    job_quality_flags (
                        job_id,
                        flag_code,
                        details,
                        generated_by
                    )

                VALUES (
                    :job_id,
                    :flag_code,

                    CAST(
                        :details
                        AS JSONB
                    ),

                    :generated_by
                )

                ON CONFLICT (
                    job_id,
                    flag_code,
                    generated_by
                )

                DO UPDATE SET
                    details =
                        EXCLUDED.details,

                    created_at =
                        NOW();
                """
            ),
            {
                "job_id":
                    job_id,

                "flag_code":
                    flag_code,

                "details":
                    json.dumps(
                        details
                    ),

                "generated_by":
                    NORMALIZATION_VERSION,
            },
        )


def _clear_stale_job_analysis(
    connection,
    job_id,
):
    # These rows are keyed directly by
    # job_id and therefore do not cascade
    # when requirement mentions are
    # replaced.
    connection.execute(
        text(
            """
            DELETE FROM
                job_profile_concept_fit

            WHERE
                job_id =
                    :job_id;
            """
        ),
        {
            "job_id":
                job_id,
        },
    )


    connection.execute(
        text(
            """
            DELETE FROM
                job_profile_fit_summary

            WHERE
                job_id =
                    :job_id;
            """
        ),
        {
            "job_id":
                job_id,
        },
    )


    connection.execute(
        text(
            """
            DELETE FROM
                job_profile_eligibility_summary

            WHERE
                job_id =
                    :job_id;
            """
        ),
        {
            "job_id":
                job_id,
        },
    )


def _store_requirements(
    connection,
    job_id,
    description,
):
    _clear_stale_job_analysis(
        connection,
        job_id,
    )


    # Re-importing the same manual job
    # replaces its derived requirement
    # representation.
    #
    # Dependent requirement-concept and
    # eligibility rows cascade.
    connection.execute(
        text(
            """
            DELETE FROM
                job_requirement_mentions

            WHERE
                job_id =
                    :job_id

                AND
                extractor_version =
                    :extractor_version;
            """
        ),
        {
            "job_id":
                job_id,

            "extractor_version":
                REQUIREMENT_VERSION,
        },
    )


    mentions = (
        extract_requirements(
            description,
            source_field="description",
        )
        if description
        else []
    )


    if description:
        mentions = (
            enrich_manual_requirement_mentions(
                description,
                mentions,
                source_field="description",
            )
        )


    mention_rows = []


    for mention in mentions:

        mention_id = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        job_requirement_mentions (
                            job_id,
                            source_field,
                            requirement_type,
                            requirement_level,
                            raw_text,
                            normalized_text,
                            structured_value,
                            rule_name,
                            extractor_version
                        )

                    VALUES (
                        :job_id,
                        'description',
                        :requirement_type,
                        :requirement_level,
                        :raw_text,
                        :normalized_text,

                        CAST(
                            :structured_value
                            AS JSONB
                        ),

                        :rule_name,
                        :extractor_version
                    )

                    RETURNING
                        requirement_mention_id;
                    """
                ),
                {
                    "job_id":
                        job_id,

                    "requirement_type":
                        mention
                        .requirement_type,

                    "requirement_level":
                        mention
                        .requirement_level,

                    "raw_text":
                        mention.raw_text,

                    "normalized_text":
                        mention
                        .normalized_text,

                    "structured_value":
                        json.dumps(
                            mention
                            .structured_value
                            or {}
                        ),

                    "rule_name":
                        mention.rule_name,

                    "extractor_version":
                        REQUIREMENT_VERSION,
                },
            )
            .scalar_one()
        )


        mention_rows.append(
            (
                mention_id,
                mention,
            )
        )


    return mention_rows


def _store_requirement_concepts(
    connection,
    mention_rows,
):
    concept_link_count = 0


    for (
        mention_id,
        mention,
    ) in mention_rows:

        candidates = (
            extract_atomic_concepts(
                mention.raw_text,
                mention
                .requirement_type,
                structured_value=(
                    mention.structured_value
                ),
            )
        )


        for candidate in candidates:

            concept_id = (
                connection.execute(
                    text(
                        """
                        INSERT INTO
                            requirement_concepts (
                                concept_type,
                                canonical_name,
                                normalized_key
                            )

                        VALUES (
                            :concept_type,
                            :canonical_name,
                            :normalized_key
                        )

                        ON CONFLICT (
                            concept_type,
                            normalized_key
                        )

                        DO UPDATE SET
                            canonical_name =
                                requirement_concepts
                                .canonical_name

                        RETURNING
                            concept_id;
                        """
                    ),
                    {
                        "concept_type":
                            candidate.get(
                                "concept_type",
                                mention
                                .requirement_type,
                            ),

                        "canonical_name":
                            candidate[
                                "raw_text"
                            ],

                        "normalized_key":
                            candidate[
                                "normalized_key"
                            ],
                    },
                )
                .scalar_one()
            )


            connection.execute(
                text(
                    """
                    INSERT INTO
                        requirement_concept_aliases (
                            concept_id,
                            alias_text,
                            normalized_alias,
                            alias_source
                        )

                    VALUES (
                        :concept_id,
                        :alias_text,
                        :normalized_alias,
                        'observed'
                    )

                    ON CONFLICT (
                        concept_id,
                        normalized_alias
                    )

                    DO NOTHING;
                    """
                ),
                {
                    "concept_id":
                        concept_id,

                    "alias_text":
                        candidate[
                            "raw_text"
                        ],

                    "normalized_alias":
                        candidate[
                            "normalized_key"
                        ],
                },
            )


            connection.execute(
                text(
                    """
                    INSERT INTO
                        job_requirement_concepts (
                            requirement_mention_id,
                            concept_id,
                            raw_concept_text,
                            extraction_method,
                            confidence,
                            extractor_version,
                            group_operator,
                            group_is_open
                        )

                    VALUES (
                        :requirement_mention_id,
                        :concept_id,
                        :raw_concept_text,
                        :extraction_method,
                        :confidence,
                        :extractor_version,
                        :group_operator,
                        :group_is_open
                    )

                    ON CONFLICT (
                        requirement_mention_id,
                        concept_id,
                        extractor_version
                    )

                    DO UPDATE SET
                        raw_concept_text =
                            EXCLUDED
                            .raw_concept_text,

                        extraction_method =
                            EXCLUDED
                            .extraction_method,

                        confidence =
                            EXCLUDED.confidence,

                        group_operator =
                            EXCLUDED
                            .group_operator,

                        group_is_open =
                            EXCLUDED
                            .group_is_open;
                    """
                ),
                {
                    "requirement_mention_id":
                        mention_id,

                    "concept_id":
                        concept_id,

                    "raw_concept_text":
                        candidate[
                            "raw_text"
                        ],

                    "extraction_method":
                        candidate.get(
                            "extraction_method",
                            "rule_based_atomic",
                        ),

                    "confidence":
                        candidate.get(
                            "confidence"
                        ),

                    "extractor_version":
                        CONCEPT_VERSION,

                    "group_operator":
                        candidate[
                            "group_operator"
                        ],

                    "group_is_open":
                        candidate[
                            "group_is_open"
                        ],
                },
            )


            concept_link_count += 1


    return concept_link_count


def import_manual_job(
    profile_id,
    listing,
    database_url=None,
):
    url = (
        listing.get(
            "url"
        )
        or ""
    ).strip()


    if not url:
        raise ValueError(
            "The imported job does not "
            "have a source URL."
        )


    description = (
        listing.get(
            "description"
        )
        or ""
    ).strip()


    title = (
        listing.get(
            "title"
        )
        or "Job listing"
    ).strip()


    company = (
        listing.get(
            "company"
        )
    )


    if isinstance(
        company,
        str,
    ):
        company = (
            company.strip()
            or None
        )


    location = (
        listing.get(
            "location"
        )
    )


    if isinstance(
        location,
        str,
    ):
        location = (
            location.strip()
            or None
        )


    source_job_id = (
        _manual_source_job_id(
            profile_id,
            url,
        )
    )


    job = NormalizedJob(
        source=
            MANUAL_SOURCE,

        source_job_id=
            source_job_id,

        job_url=
            url,

        title=
            title,

        company_name=
            company,

        location_raw=
            location,

        location_country=
            None,

        employment_type=
            listing.get(
                "employment_type"
            ),

        salary_text=
            None,

        description=
            description,

        date_posted=
            _parse_date(
                listing.get(
                    "date_posted"
                )
            ),

        metadata={
            "manual_import":
                True,

            "extraction_method":
                listing.get(
                    "extraction_method"
                ),

            "source_url":
                url,
        },
    )


    engine = create_database_engine(
        database_url
    )


    with engine.begin() as connection:

        job_id = upsert_job(
            connection,
            job,
        )


        existing_import = (
            connection.execute(
                text(
                    """
                    SELECT
                        manual_job_import_id

                    FROM
                        manual_job_imports

                    WHERE
                        profile_id =
                            :profile_id

                        AND
                        job_id =
                            :job_id;
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


        connection.execute(
            text(
                """
                INSERT INTO
                    manual_job_imports (
                        profile_id,
                        job_id,
                        source_url,
                        extraction_method
                    )

                VALUES (
                    :profile_id,
                    :job_id,
                    :source_url,
                    :extraction_method
                )

                ON CONFLICT (
                    profile_id,
                    job_id
                )

                DO UPDATE SET
                    source_url =
                        EXCLUDED.source_url,

                    extraction_method =
                        EXCLUDED
                        .extraction_method,

                    updated_at =
                        NOW();
                """
            ),
            {
                "profile_id":
                    profile_id,

                "job_id":
                    job_id,

                "source_url":
                    url,

                "extraction_method":
                    (
                        listing.get(
                            "extraction_method"
                        )
                        or "unknown"
                    ),
            },
        )


        _normalize_imported_job(
            connection,
            job_id,
        )


        mention_rows = (
            _store_requirements(
                connection,
                job_id,
                description,
            )
        )


        concept_link_count = (
            _store_requirement_concepts(
                connection,
                mention_rows,
            )
        )


        stored = (
            connection.execute(
                text(
                    """
                    SELECT
                        j.job_id,
                        j.raw_title,
                        j.raw_company_name,
                        j.location_raw,
                        j.employment_type,
                        j.description,
                        j.job_url,
                        j.source,
                        j.date_posted,
                        j.derived_posted_date,

                        EXISTS (
                            SELECT 1

                            FROM
                                job_quality_flags q

                            WHERE
                                q.job_id =
                                    j.job_id

                                AND
                                q.generated_by =
                                    'normalize_v1'

                                AND
                                q.flag_code =
                                    'insufficient_description'
                        )
                        AS insufficient_description

                    FROM jobs j

                    WHERE
                        j.job_id =
                            :job_id;
                    """
                ),
                {
                    "job_id":
                        job_id,
                },
            )
            .mappings()
            .one()
        )


    return {
        "created":
            existing_import
            is None,

        "job":
            dict(
                stored
            ),

        "requirement_count":
            len(
                mention_rows
            ),

        "concept_link_count":
            concept_link_count,
    }


def list_manual_jobs(
    profile_id,
    database_url=None,
):
    engine = create_database_engine(
        database_url
    )


    with engine.connect() as connection:

        rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        m.manual_job_import_id,
                        m.imported_at,
                        m.updated_at,
                        m.extraction_method,

                        j.job_id,
                        j.raw_title,
                        j.raw_company_name,
                        j.location_raw,
                        j.employment_type,
                        j.job_url,
                        j.source,
                        j.date_posted,
                        j.derived_posted_date,

                        (
                            SELECT COUNT(*)

                            FROM
                                job_requirement_mentions r

                            WHERE
                                r.job_id =
                                    j.job_id

                                AND
                                r.extractor_version =
                                    :requirement_version
                        )
                        AS requirement_count

                    FROM
                        manual_job_imports m

                    JOIN jobs j
                        ON
                            j.job_id =
                            m.job_id

                    WHERE
                        m.profile_id =
                            :profile_id

                    ORDER BY
                        m.updated_at DESC,
                        m.manual_job_import_id DESC;
                    """
                ),
                {
                    "profile_id":
                        profile_id,

                    "requirement_version":
                        REQUIREMENT_VERSION,
                },
            )
            .mappings()
            .all()
        )


    return [
        dict(
            row
        )
        for row in rows
    ]


def get_manual_job(
    profile_id,
    job_id,
    database_url=None,
):
    engine = create_database_engine(
        database_url
    )


    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        m.manual_job_import_id,
                        m.imported_at,
                        m.updated_at,
                        m.extraction_method,

                        j.job_id,
                        j.raw_title,
                        j.raw_company_name,
                        j.location_raw,
                        j.employment_type,
                        j.description,
                        j.job_url,
                        j.source,
                        j.date_posted,
                        j.derived_posted_date,

                        COALESCE(
                            (
                                SELECT
                                    jsonb_agg(
                                        jsonb_build_object(
                                            'id',
                                                r.requirement_mention_id,

                                            'type',
                                                r.requirement_type,

                                            'level',
                                                r.requirement_level,

                                            'text',
                                                r.raw_text,

                                            'structured_value',
                                                r.structured_value
                                        )

                                        ORDER BY
                                            r.requirement_mention_id
                                    )

                                FROM
                                    job_requirement_mentions r

                                WHERE
                                    r.job_id =
                                        j.job_id

                                    AND
                                    r.extractor_version =
                                        :requirement_version
                            ),

                            '[]'::jsonb
                        )
                        AS requirements

                    FROM
                        manual_job_imports m

                    JOIN jobs j
                        ON
                            j.job_id =
                            m.job_id

                    WHERE
                        m.profile_id =
                            :profile_id

                        AND
                        m.job_id =
                            :job_id;
                    """
                ),
                {
                    "profile_id":
                        profile_id,

                    "job_id":
                        job_id,

                    "requirement_version":
                        REQUIREMENT_VERSION,
                },
            )
            .mappings()
            .one_or_none()
        )


    if row is None:
        return None


    return dict(
        row
    )
