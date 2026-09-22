-- 020_add_manual_job_imports.sql
--
-- Records ownership of jobs manually imported from a public listing URL.
-- The job itself still uses the shared CareerCompass `jobs` model so the
-- existing requirements, matching and application tables can reference it.

CREATE TABLE IF NOT EXISTS manual_job_imports (
    manual_job_import_id BIGSERIAL PRIMARY KEY,

    profile_id BIGINT NOT NULL
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    job_id BIGINT NOT NULL
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    source_url TEXT NOT NULL,

    extraction_method TEXT NOT NULL,

    imported_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    UNIQUE (
        profile_id,
        job_id
    )
);


CREATE INDEX IF NOT EXISTS
    idx_manual_job_imports_profile
ON manual_job_imports (
    profile_id,
    imported_at DESC
);


CREATE INDEX IF NOT EXISTS
    idx_manual_job_imports_job
ON manual_job_imports (
    job_id
);


-- The browser does not need direct table access.
-- Server-side database connections can continue to manage the table.
ALTER TABLE manual_job_imports
ENABLE ROW LEVEL SECURITY;
