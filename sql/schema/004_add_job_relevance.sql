CREATE TABLE IF NOT EXISTS job_relevance_scores (
    search_request_id BIGINT NOT NULL
        REFERENCES search_requests(search_request_id)
        ON DELETE CASCADE,

    job_id BIGINT NOT NULL
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    scoring_method TEXT NOT NULL,

    model_name TEXT NOT NULL,

    title_score DOUBLE PRECISION NOT NULL,

    description_score DOUBLE PRECISION,

    combined_score DOUBLE PRECISION NOT NULL,

    rank_position INTEGER,

    scoring_version TEXT NOT NULL,

    scored_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (
        search_request_id,
        job_id,
        scoring_method,
        model_name
    )
);


CREATE INDEX IF NOT EXISTS
    idx_job_relevance_search
ON job_relevance_scores(search_request_id);


CREATE INDEX IF NOT EXISTS
    idx_job_relevance_score
ON job_relevance_scores(
    search_request_id,
    combined_score DESC
);