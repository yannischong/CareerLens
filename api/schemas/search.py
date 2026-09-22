from typing import Literal

from pydantic import BaseModel, Field


class JobSearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=200,
    )

    location: str = Field(
        default="Singapore",
        min_length=1,
        max_length=200,
    )

    country: str = Field(
        default="sg",
        min_length=2,
        max_length=2,
    )

    providers: list[
        Literal[
            "serpapi",
            "jooble",
        ]
    ] = Field(
        default_factory=lambda: [
            "serpapi",
            "jooble",
        ],
        min_length=1,
        max_length=2,
    )

    pages: Literal[1] = 1