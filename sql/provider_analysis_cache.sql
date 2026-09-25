-- CareerLens provider AI analysis cache
--
-- Run once in the Supabase SQL Editor.
-- These tables cache model-refined job extraction globally by job and
-- resume-specific fit analysis by profile/resume.

CREATE TABLE IF NOT EXISTS
    provider_job_analysis_cache (
        job_id BIGINT NOT NULL,
        job_content_hash TEXT NOT NULL,
        analysis_version TEXT NOT NULL,
        analysis_method TEXT NOT NULL,
        requirements JSONB NOT NULL DEFAULT '[]'::JSONB,
        skills JSONB NOT NULL DEFAULT '[]'::JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

        PRIMARY KEY (
            job_id,
            job_content_hash,
            analysis_version
        )
    );


CREATE INDEX IF NOT EXISTS
    idx_provider_job_analysis_cache_job
ON
    provider_job_analysis_cache (
        job_id,
        analysis_version
    );


CREATE TABLE IF NOT EXISTS
    provider_profile_analysis_cache (
        profile_id BIGINT NOT NULL,
        job_id BIGINT NOT NULL,
        resume_id BIGINT NOT NULL,
        job_content_hash TEXT NOT NULL,
        job_analysis_version TEXT NOT NULL,
        fit_version TEXT NOT NULL,
        analysis_payload JSONB NOT NULL,
        resume_match_percentage NUMERIC(5, 2),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

        PRIMARY KEY (
            profile_id,
            job_id,
            resume_id,
            job_content_hash,
            job_analysis_version,
            fit_version
        )
    );


CREATE INDEX IF NOT EXISTS
    idx_provider_profile_analysis_cache_lookup
ON
    provider_profile_analysis_cache (
        profile_id,
        resume_id,
        job_id,
        fit_version
    );
