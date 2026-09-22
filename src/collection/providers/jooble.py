import requests

from src.collection.models import (
    NormalizedJob,
    ProviderPage,
)


def search_jooble(
    query,
    location,
    api_key,
    base_url,
    max_pages,
):
    results_per_page = 50

    endpoint = (
        f"{base_url.rstrip('/')}/api/{api_key}"
    )

    for page in range(
        1,
        max_pages + 1,
    ):
        body = {
            "keywords": query,
            "location": location,
            "page": page,
            "ResultOnPage": results_per_page,
            "companysearch": False,
        }

        response = requests.post(
            endpoint,
            json=body,
            timeout=30,
        )

        response.raise_for_status()

        payload = response.json()

        raw_jobs = payload.get(
            "jobs",
            [],
        )

        jobs = []

        for raw_job in raw_jobs:
            source_job_id = str(
                raw_job.get(
                    "id",
                    "",
                )
            ).strip()

            title = (
                raw_job.get("title")
                or ""
            ).strip()

            job_url = (
                raw_job.get("link")
                or ""
            ).strip()

            if (
                not source_job_id
                or not title
                or not job_url
            ):
                continue

            company_name = (
                raw_job.get("company")
                or (
                    "Unknown Company "
                    f"[Jooble:{source_job_id}]"
                )
            ).strip()

            jobs.append(
                NormalizedJob(
                    source="Jooble",
                    source_job_id=(
                        source_job_id
                    ),
                    job_url=job_url,
                    title=title,
                    company_name=(
                        company_name
                    ),
                    location_raw=(
                        raw_job.get(
                            "location"
                        )
                    ),
                    location_country=(
                        "Singapore"
                    ),
                    employment_type=(
                        raw_job.get("type")
                    ),
                    salary_text=(
                        raw_job.get("salary")
                    ),
                    description=(
                        raw_job.get(
                            "snippet"
                        )
                    ),
                    date_posted=None,
                    metadata={
                        "provider_source":
                            raw_job.get(
                                "source"
                            ),
                        "provider_updated":
                            raw_job.get(
                                "updated"
                            ),
                        "description_type":
                            "snippet",
                    },
                )
            )

        yield ProviderPage(
            page_number=page,
            payload=payload,
            jobs=jobs,
            reported_count=(
                payload.get(
                    "totalCount"
                )
            ),
        )

        if (
            len(raw_jobs)
            < results_per_page
        ):
            break