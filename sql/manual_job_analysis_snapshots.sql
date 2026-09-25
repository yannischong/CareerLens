CREATE TABLE IF NOT EXISTS manual_job_analysis_snapshots (
    profile_id BIGINT NOT NULL
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    job_id BIGINT NOT NULL
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    listing_snapshot JSONB NOT NULL
        DEFAULT '{}'::JSONB,

    resume_fit_snapshot JSONB,

    resume_id BIGINT
        REFERENCES resume_documents(resume_id)
        ON DELETE SET NULL,

    analysis_version TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    PRIMARY KEY (profile_id, job_id)
);

CREATE INDEX IF NOT EXISTS
    idx_manual_job_analysis_snapshots_job
ON manual_job_analysis_snapshots(job_id);

CREATE INDEX IF NOT EXISTS
    idx_manual_job_analysis_snapshots_resume
ON manual_job_analysis_snapshots(profile_id, resume_id);

ALTER TABLE manual_job_analysis_snapshots
ENABLE ROW LEVEL SECURITY;
