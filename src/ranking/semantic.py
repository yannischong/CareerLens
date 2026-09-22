import os

from src.ranking.lexical import (
    calculate_tfidf_scores,
)


FULL_MODEL_NAME = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)

LIGHTWEIGHT_MODEL_NAME = (
    "lightweight_tfidf_proxy"
)

LIGHTWEIGHT_MODE = (
    os.getenv(
        "LIGHTWEIGHT_MODE",
        "false",
    )
    .strip()
    .lower()
    in {
        "1",
        "true",
        "yes",
        "on",
    }
)

MODEL_NAME = (
    LIGHTWEIGHT_MODEL_NAME
    if LIGHTWEIGHT_MODE
    else FULL_MODEL_NAME
)


def calculate_semantic_scores(
    query,
    jobs,
):
    if LIGHTWEIGHT_MODE:
        return calculate_tfidf_scores(
            query,
            jobs,
        )

    try:
        from sentence_transformers import (
            SentenceTransformer,
        )
    except ImportError:
        return calculate_tfidf_scores(
            query,
            jobs,
        )

    model = SentenceTransformer(
        FULL_MODEL_NAME
    )

    titles = [
        job["normalized_title"]
        or job["raw_title"]
        or ""
        for job in jobs
    ]

    descriptions = [
        job["normalized_description"]
        or job["description"]
        or ""
        for job in jobs
    ]

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True,
    )

    title_embeddings = model.encode(
        titles,
        normalize_embeddings=True,
    )

    description_embeddings = (
        model.encode(
            descriptions,
            normalize_embeddings=True,
        )
    )

    title_scores = (
        query_embedding
        @ title_embeddings.T
    )[0]

    description_scores = (
        query_embedding
        @ description_embeddings.T
    )[0]

    results = []

    for index, job in enumerate(jobs):
        title_score = float(
            title_scores[index]
        )

        description_score = float(
            description_scores[index]
        )

        combined_score = (
            0.65 * title_score
            + 0.35 * description_score
        )

        results.append(
            {
                "job_id":
                    job["job_id"],
                "title_score":
                    title_score,
                "description_score":
                    description_score,
                "combined_score":
                    combined_score,
            }
        )

    return results
