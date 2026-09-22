from datetime import datetime
from urllib.parse import urlparse

from src.cleaning.normalization import (
    extract_recruiting_cycle_years,
    get_metadata,
    relative_age_days,
)


MIN_ASSESSABLE_DESCRIPTION_CHARS = 700


def get_apply_domains(
    metadata,
):
    metadata = get_metadata(
        metadata
    )

    apply_options = metadata.get(
        "apply_options"
    ) or []

    domains = []

    for option in apply_options:

        link = option.get(
            "link"
        )

        if not link:
            continue

        domain = urlparse(
            link
        ).netloc.casefold()

        if domain.startswith(
            "www."
        ):
            domain = domain[4:]

        if domain:
            domains.append(
                domain
            )

    return sorted(
        set(domains)
    )


def build_quality_flags(
    job,
):
    flags = []

    current_year = (
        datetime.now().year
    )

    description = (
        job["description"]
        or ""
    ).strip()

    metadata = get_metadata(
        job["source_metadata"]
    )


    # Completely missing description.
    if not description:

        flags.append(
            (
                "missing_description",
                {},
            )
        )


    # A provider may explicitly tell us
    # that the supplied text is only a
    # search-result snippet.
    description_type = (
        metadata.get(
            "description_type"
        )
    )


    if (
        description
        and
        (
            description_type == "snippet"

            or len(description)
            <
            MIN_ASSESSABLE_DESCRIPTION_CHARS
        )
    ):

        reasons = []

        if description_type == "snippet":
            reasons.append(
                "provider_snippet"
            )

        if (
            len(description)
            <
            MIN_ASSESSABLE_DESCRIPTION_CHARS
        ):
            reasons.append(
                "short_description"
            )

        flags.append(
            (
                "insufficient_description",
                {
                    "description_chars":
                        len(description),

                    "minimum_chars":
                        MIN_ASSESSABLE_DESCRIPTION_CHARS,

                    "description_type":
                        description_type,

                    "reasons":
                        reasons,
                },
            )
        )


    if not job["location_raw"]:

        flags.append(
            (
                "missing_location",
                {},
            )
        )


    company_name = (
        job["raw_company_name"]
        or ""
    )

    if company_name.startswith(
        "Unknown Company"
    ):

        flags.append(
            (
                "unknown_company",
                {},
            )
        )


    cycle_years = (
        extract_recruiting_cycle_years(
            job["raw_title"]
        )
    )

    past_cycle_years = [
        year
        for year in cycle_years
        if year < current_year
    ]


    if past_cycle_years:

        flags.append(
            (
                "past_recruiting_cycle",
                {
                    "years":
                        past_cycle_years,

                    "current_year":
                        current_year,
                },
            )
        )


    relative_days = (
        relative_age_days(
            job["source_metadata"]
        )
    )


    if (
        past_cycle_years
        and relative_days is not None
        and relative_days <= 30
    ):

        flags.append(
            (
                "conflicting_freshness_signals",
                {
                    "past_cycle_years":
                        past_cycle_years,

                    "provider_age_days":
                        relative_days,
                },
            )
        )


    apply_domains = (
        get_apply_domains(
            job["source_metadata"]
        )
    )


    if len(apply_domains) > 1:

        flags.append(
            (
                "multiple_apply_domains",
                {
                    "domains":
                        apply_domains,

                    "count":
                        len(
                            apply_domains
                        ),
                },
            )
        )


    posted_at = metadata.get(
        "posted_at"
    )


    if (
        posted_at
        and relative_days is None
    ):

        flags.append(
            (
                "unparsed_provider_posted_at",
                {
                    "posted_at":
                        posted_at,
                },
            )
        )


    return flags