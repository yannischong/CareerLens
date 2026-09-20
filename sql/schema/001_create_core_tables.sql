CREATE TABLE IF NOT EXISTS companies (
    company_id BIGSERIAL PRIMARY KEY,
    canonical_name TEXT NOT NULL UNIQUE,
    industry TEXT,
    company_type TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id BIGSERIAL PRIMARY KEY,

    company_id BIGINT NOT NULL
        REFERENCES companies(company_id)
        ON DELETE RESTRICT,

    raw_company_name TEXT NOT NULL,

    source TEXT NOT NULL,
    source_job_id TEXT,
    job_url TEXT NOT NULL,

    raw_title TEXT NOT NULL,
    canonical_role TEXT,

    location_raw TEXT,
    location_country TEXT,

    employment_type TEXT,
    seniority TEXT,
    salary_text TEXT,

    description TEXT,
    requirements_text TEXT,
    education_requirements TEXT,
    experience_requirements TEXT,

    date_posted DATE,
    closing_date DATE,

    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT valid_closing_date
        CHECK (
            closing_date IS NULL
            OR date_posted IS NULL
            OR closing_date >= date_posted
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_jobs_source_job_id
ON jobs (source, source_job_id)
WHERE source_job_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_jobs_company_id
    ON jobs (company_id);

CREATE INDEX IF NOT EXISTS idx_jobs_canonical_role
    ON jobs (canonical_role);

CREATE INDEX IF NOT EXISTS idx_jobs_date_posted
    ON jobs (date_posted);

CREATE INDEX IF NOT EXISTS idx_jobs_source
    ON jobs (source);