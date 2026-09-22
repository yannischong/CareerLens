import requests

from src.collection.models import (
    NormalizedJob,
    ProviderPage,
)


def search_serpapi(
    query,
    location,
    country_code,
    api_key,
    max_pages,
):
    next_page_token = None

    for page in range(1, max_pages + 1):

        params = {
            "engine": "google_jobs",
            "q": query,
            "location": location,
            "gl": country_code.lower(),
            "hl": "en",
            "google_domain": "google.com.sg",
            "api_key": api_key,
        }

        if next_page_token:
            params["next_page_token"] = (
                next_page_token
            )

        response = requests.get(
            "https://serpapi.com/search.json",
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        payload = response.json()

        raw_jobs = payload.get(
            "jobs_results",
            [],
        )

        jobs = []

        for raw_job in raw_jobs:

            source_job_id = (
                raw_job.get("job_id")
                or ""
            ).strip()

            title = (
                raw_job.get("title")
                or ""
            ).strip()

            company_name = (
                raw_job.get("company_name")
                or ""
            ).strip()

            if not company_name:
                company_name = (
                    "Unknown Company "
                    f"[SerpApi:{source_job_id}]"
                )

            apply_options = (
                raw_job.get("apply_options")
                or []
            )

            job_url = None

            if apply_options:
                job_url = (
                    apply_options[0]
                    .get("link")
                )

            if not job_url:
                job_url = raw_job.get(
                    "share_link"
                )

            if (
                not source_job_id
                or not title
                or not job_url
            ):
                continue

            detected = (
                raw_job.get(
                    "detected_extensions"
                )
                or {}
            )

            jobs.append(
                NormalizedJob(
                    source=
                        "SerpApi Google Jobs",

                    source_job_id=
                        source_job_id,

                    job_url=job_url,

                    title=title,

                    company_name=
                        company_name,

                    location_raw=
                        raw_job.get("location"),

                    location_country=
                        "Singapore",

                    employment_type=
                        detected.get(
                            "schedule_type"
                        ),

                    salary_text=
                        detected.get("salary"),

                    description=
                        raw_job.get(
                            "description"
                        ),

                    date_posted=None,

                    metadata={
                        "via":
                            raw_job.get("via"),

                        "posted_at":
                            detected.get(
                                "posted_at"
                            ),

                        "work_from_home":
                            detected.get(
                                "work_from_home"
                            ),

                        "apply_options":
                            apply_options,

                        "share_link":
                            raw_job.get(
                                "share_link"
                            ),
                    },
                )
            )

        yield ProviderPage(
            page_number=page,
            payload=payload,
            jobs=jobs,
        )

        pagination = (
            payload.get(
                "serpapi_pagination"
            )
            or {}
        )

        next_page_token = (
            pagination.get(
                "next_page_token"
            )
        )

        if (
            not raw_jobs
            or not next_page_token
        ):
            break