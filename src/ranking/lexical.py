from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_tfidf_scores(
    query,
    jobs,
):
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

    title_documents = [
        query,
        *titles,
    ]

    title_vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
    )

    title_matrix = (
        title_vectorizer.fit_transform(
            title_documents
        )
    )

    title_scores = cosine_similarity(
        title_matrix[0:1],
        title_matrix[1:],
    )[0]


    description_documents = [
        query,
        *descriptions,
    ]

    description_vectorizer = (
        TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
        )
    )

    description_matrix = (
        description_vectorizer.fit_transform(
            description_documents
        )
    )

    description_scores = cosine_similarity(
        description_matrix[0:1],
        description_matrix[1:],
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