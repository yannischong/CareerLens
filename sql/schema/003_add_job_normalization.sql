-- Derived fields only.
-- Original provider fields remain untouched.

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS normalized_title TEXT;

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS normalized_company_name TEXT;

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS normalized_location TEXT;

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS normalized_description TEXT;

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS derived_posted_date DATE;

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS derived_posted_date_method TEXT;

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS normalization_version TEXT;

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS normalized_at TIMESTAMPTZ;


-- Quality problems detected automatically.
CREATE TABLE IF NOT EXISTS job_quality_flags (
    job_id BIGINT NOT NULL
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    flag_code TEXT NOT NULL,

    details JSONB NOT NULL
        DEFAULT '{}'::JSONB,

    generated_by TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    PRIMARY KEY (
        job_id,
        flag_code,
        generated_by
    )
);


-- Possible duplicates across different providers.
-- Nothing is automatically merged.
CREATE TABLE IF NOT EXISTS duplicate_candidates (
    job_id_a BIGINT NOT NULL
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    job_id_b BIGINT NOT NULL
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    company_similarity NUMERIC(5,2)
        NOT NULL,

    title_similarity NUMERIC(5,2)
        NOT NULL,

    location_match BOOLEAN,

    date_gap_days INTEGER,

    match_method TEXT NOT NULL,

    review_status TEXT NOT NULL
        DEFAULT 'unreviewed',

    detected_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    PRIMARY KEY (
        job_id_a,
        job_id_b
    ),

    CONSTRAINT ordered_duplicate_pair
        CHECK (job_id_a < job_id_b),

    CONSTRAINT valid_duplicate_review_status
        CHECK (
            review_status IN (
                'unreviewed',
                'confirmed',
                'not_duplicate'
            )
        )
);


CREATE INDEX IF NOT EXISTS
    idx_jobs_normalized_company
ON jobs(normalized_company_name);


CREATE INDEX IF NOT EXISTS
    idx_jobs_normalized_title
ON jobs(normalized_title);


CREATE INDEX IF NOT EXISTS
    idx_job_quality_flags_code
ON job_quality_flags(flag_code);