import argparse
import json
import re

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import create_database_engine
from src.ranking.lexical import calculate_tfidf_scores
from src.ranking.semantic import MODEL_NAME, calculate_semantic_scores


SCORING_VERSION = "relevance_v1"

ROLE_STOPWORDS = {"a", "an", "and", "at", "for", "in", "of", "on", "the"}
ROLE_EQUIVALENTS = {
    "engineering": "engineer",
    "developer": "engineer",
    "development": "engineer",
    "trading": "trader",
    "quant": "quantitative",
}
EARLY_CAREER_TERMS = {"intern", "internship", "graduate", "campus", "student", "trainee"}
SENIORITY_TERMS = {"senior", "sr", "lead", "principal", "staff", "manager", "director", "head"}

load_dotenv()


def _normalise_token(token):
    token = token.lower().strip("-_/.,()[]{}")
    return ROLE_EQUIVALENTS.get(token, token)


def _role_tokens(value):
    return {
        _normalise_token(token)
        for token in re.findall(r"[a-zA-Z0-9+#.-]+", value or "")
        if _normalise_token(token) and _normalise_token(token) not in ROLE_STOPWORDS
    }


def _title_match(query, title):
    query_tokens = _role_tokens(query)
    title_tokens = _role_tokens(title)
    if not query_tokens or not title_tokens:
        return 0.0

    overlap = len(query_tokens & title_tokens) / len(query_tokens)
    query_early = bool(query_tokens & EARLY_CAREER_TERMS)
    title_early = bool(title_tokens & EARLY_CAREER_TERMS)
    title_senior = bool(title_tokens & SENIORITY_TERMS)

    if query_early and title_senior and not title_early:
        return 0.0
    if query_early and not title_early:
        overlap *= 0.60
    return overlap


def _metadata(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, ValueError):
            return {}
    return {}


def _quality_adjustment(query, location, job):
    """Add modest, explainable search-quality signals to semantic relevance."""
    source = (job.get("source") or "").strip()
    title = job.get("normalized_title") or job.get("raw_title") or ""
    description = job.get("normalized_description") or job.get("description") or ""
    job_location = (job.get("location_raw") or "").lower()
    metadata = _metadata(job.get("source_metadata"))

    adjustment = 0.0
    title_match = _title_match(query, title)

    adjustment += 0.10 * title_match
    if title_match < 0.50:
        adjustment -= 0.12

    requested_location = (location or "").strip().lower()
    if requested_location:
        if requested_location in job_location:
            adjustment += 0.035
        elif job_location:
            adjustment -= 0.035

    description_length = len((description or "").strip())
    if description_length >= 1000:
        adjustment += 0.035
    elif description_length < 300:
        adjustment -= 0.055

    # Web Discovery only reaches this pool after the actual CareerCompass reader
    # has successfully retrieved >= 1000 characters of listing content.
    if source == "SerpApi Web Discovery" and metadata.get("directly_analysable"):
        adjustment += 0.075

    # Jooble currently stores provider snippets, not verified complete listings.
    # This is intentionally modest: strong Jooble matches can still rank highly.
    if source == "Jooble" and metadata.get("description_type") == "snippet":
        adjustment -= 0.045

    return adjustment


def rank_search(search_request_id, database_url=None):
    engine = create_database_engine(database_url)

    with engine.connect() as connection:
        search_request = connection.execute(
            text(
                """
                SELECT search_request_id, query_text, location_text
                FROM search_requests
                WHERE search_request_id = :search_request_id;
                """
            ),
            {"search_request_id": search_request_id},
        ).mappings().first()

    if search_request is None:
        raise ValueError("Search request not found.")

    query = search_request["query_text"]
    location = search_request["location_text"] or ""

    with engine.connect() as connection:
        jobs = connection.execute(
            text(
                """
                SELECT DISTINCT
                    j.job_id,
                    j.raw_title,
                    j.normalized_title,
                    j.description,
                    j.normalized_description,
                    j.raw_company_name,
                    j.location_raw,
                    j.source,
                    j.source_metadata
                FROM jobs AS j
                JOIN source_search_results AS ssres
                    ON j.job_id = ssres.job_id
                JOIN source_search_runs AS ssr
                    ON ssres.source_search_run_id = ssr.source_search_run_id
                WHERE ssr.search_request_id = :search_request_id
                ORDER BY j.job_id;
                """
            ),
            {"search_request_id": search_request_id},
        ).mappings().all()

    if not jobs:
        raise ValueError("No jobs found for this search request.")

    print(f"Search query: {query}")
    print(f"Jobs to rank: {len(jobs)}")

    tfidf_results = calculate_tfidf_scores(query, jobs)
    semantic_results = calculate_semantic_scores(query, jobs)
    jobs_by_id = {job["job_id"]: job for job in jobs}

    def add_quality_adjustments(results):
        adjusted = []
        for result in results:
            item = dict(result)
            item["combined_score"] = float(item["combined_score"]) + _quality_adjustment(
                query,
                location,
                jobs_by_id[item["job_id"]],
            )
            adjusted.append(item)
        return adjusted

    tfidf_results = add_quality_adjustments(tfidf_results)
    semantic_results = add_quality_adjustments(semantic_results)

    def store_scores(method, model_name, results):
        ranked_results = sorted(results, key=lambda result: result["combined_score"], reverse=True)

        with engine.begin() as connection:
            for rank, result in enumerate(ranked_results, start=1):
                connection.execute(
                    text(
                        """
                        INSERT INTO job_relevance_scores (
                            search_request_id, job_id, scoring_method, model_name,
                            title_score, description_score, combined_score,
                            rank_position, scoring_version
                        )
                        VALUES (
                            :search_request_id, :job_id, :scoring_method, :model_name,
                            :title_score, :description_score, :combined_score,
                            :rank_position, :scoring_version
                        )
                        ON CONFLICT (search_request_id, job_id, scoring_method, model_name)
                        DO UPDATE SET
                            title_score = EXCLUDED.title_score,
                            description_score = EXCLUDED.description_score,
                            combined_score = EXCLUDED.combined_score,
                            rank_position = EXCLUDED.rank_position,
                            scoring_version = EXCLUDED.scoring_version,
                            scored_at = NOW();
                        """
                    ),
                    {
                        "search_request_id": search_request_id,
                        "job_id": result["job_id"],
                        "scoring_method": method,
                        "model_name": model_name,
                        "title_score": result["title_score"],
                        "description_score": result["description_score"],
                        "combined_score": result["combined_score"],
                        "rank_position": rank,
                        "scoring_version": SCORING_VERSION,
                    },
                )

    store_scores("tfidf", "tfidf_1_2gram", tfidf_results)
    store_scores("semantic", MODEL_NAME, semantic_results)

    print("Stored TF-IDF and semantic rankings with search-quality adjustments.")

    return {"search_request_id": search_request_id, "jobs_ranked": len(jobs)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rank CareerCompass search results against the user's occupation query."
    )
    parser.add_argument("--search-request-id", type=int, required=True)
    args = parser.parse_args()
    rank_search(search_request_id=args.search_request_id)
