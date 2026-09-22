import argparse

from src.services.job_search_service import (
    run_job_search,
)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Search multiple job providers "
            "and store results in CareerCompass."
        )
    )

    parser.add_argument(
        "--query",
        required=True,
    )

    parser.add_argument(
        "--location",
        default="Singapore",
    )

    parser.add_argument(
        "--country",
        default="sg",
    )

    parser.add_argument(
        "--providers",
        nargs="+",
        choices=[
            "serpapi",
            "jooble",
        ],
        default=[
            "serpapi",
            "jooble",
        ],
    )

    parser.add_argument(
        "--pages",
        type=int,
        default=1,
    )

    args = parser.parse_args()


    result = run_job_search(
        query=args.query,
        location=args.location,
        country=args.country,
        providers=args.providers,
        pages=args.pages,
    )


    print(
        f"Search request: "
        f"{result['search_request_id']}"
    )

    print(
        f"Query: "
        f"{result['query']}"
    )

    print(
        f"Location: "
        f"{result['location']}"
    )


    for provider in (
        result["providers"]
    ):

        print()

        print(
            f"--- "
            f"{provider['provider'].upper()} "
            f"---"
        )

        print(
            f"Status: "
            f"{provider['status']}"
        )

        print(
            f"Pages: "
            f"{provider['pages_fetched']}"
        )

        print(
            f"Jobs: "
            f"{provider['jobs_returned']}"
        )


        if provider["error"]:

            print(
                f"Error: "
                f"{provider['error']}"
            )


    print()
    print(
        "CareerCompass search complete."
    )


if __name__ == "__main__":
    main()