from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class NormalizedJob:
    source: str
    source_job_id: str

    job_url: str

    title: str
    company_name: str

    location_raw: str | None
    location_country: str | None

    employment_type: str | None
    salary_text: str | None

    description: str | None
    date_posted: date | None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ProviderPage:
    page_number: int
    payload: dict
    jobs: list[NormalizedJob]

    reported_count: int | None = None