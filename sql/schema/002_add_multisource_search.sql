-- Store provider-specific information that does not fit
-- neatly into CareerLens' common job schema.
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS source_metadata JSONB
NOT NULL DEFAULT '{}'::JSONB;


-- One request made by the CareerLens user.
-- Example:
-- "Data Analyst", Singapore
CREATE TABLE IF NOT EXISTS search_requests (
    search_request_id BIGSERIAL PRIMARY KEY,

    query_text TEXT NOT NULL,
    location_text TEXT NOT NULL,
    country_code TEXT NOT NULL,

    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- One search request can be sent to multiple providers.
CREATE TABLE IF NOT EXISTS source_search_runs (
    source_search_run_id BIGSERIAL PRIMARY KEY,

    search_request_id BIGINT NOT NULL
        REFERENCES search_requests(search_request_id)
        ON DELETE CASCADE,

    source TEXT NOT NULL,

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    reported_count INTEGER,
    pages_fetched INTEGER NOT NULL DEFAULT 0,
    jobs_returned INTEGER NOT NULL DEFAULT 0,

    status TEXT NOT NULL DEFAULT 'running',

    error_message TEXT,
    raw_response_dir TEXT,

    CONSTRAINT valid_source_search_status
        CHECK (
            status IN (
                'running',
                'completed',
                'failed',
                'skipped'
            )
        )
);


-- Records which jobs were returned by a provider search.
CREATE TABLE IF NOT EXISTS source_search_results (
    source_search_run_id BIGINT NOT NULL
        REFERENCES source_search_runs(source_search_run_id)
        ON DELETE CASCADE,

    job_id BIGINT NOT NULL
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    page_number INTEGER NOT NULL,
    result_rank INTEGER NOT NULL,

    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (
        source_search_run_id,
        job_id
    )
);


CREATE INDEX IF NOT EXISTS idx_search_requests_query
ON search_requests(query_text);

CREATE INDEX IF NOT EXISTS idx_search_requests_requested_at
ON search_requests(requested_at);

CREATE INDEX IF NOT EXISTS idx_source_search_runs_request
ON source_search_runs(search_request_id);

CREATE INDEX IF NOT EXISTS idx_source_search_results_job
ON source_search_results(job_id);