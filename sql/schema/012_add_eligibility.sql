CREATE TABLE IF NOT EXISTS profile_eligibility_facts (
    fact_id BIGSERIAL PRIMARY KEY,

    profile_id BIGINT NOT NULL
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    fact_type TEXT NOT NULL,

    fact_value JSONB NOT NULL,

    raw_text TEXT,

    source_type TEXT NOT NULL,

    review_status TEXT NOT NULL
        DEFAULT 'candidate',

    extractor_version TEXT,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    CONSTRAINT valid_profile_fact_status
        CHECK (
            review_status IN (
                'confirmed',
                'candidate',
                'rejected'
            )
        )
);


CREATE TABLE IF NOT EXISTS job_eligibility_requirements (
    eligibility_requirement_id BIGSERIAL PRIMARY KEY,

    requirement_mention_id BIGINT NOT NULL
        REFERENCES job_requirement_mentions(
            requirement_mention_id
        )
        ON DELETE CASCADE,

    fact_type TEXT NOT NULL,

    comparison_operator TEXT NOT NULL,

    requirement_value JSONB NOT NULL
        DEFAULT '{}'::JSONB,

    extractor_version TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    CONSTRAINT valid_eligibility_operator
        CHECK (
            comparison_operator IN (
                'gte',
                'eq',
                'between',
                'boolean',
                'manual_review'
            )
        )
);


CREATE TABLE IF NOT EXISTS job_profile_eligibility_checks (
    profile_id BIGINT NOT NULL
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    eligibility_requirement_id BIGINT NOT NULL
        REFERENCES job_eligibility_requirements(
            eligibility_requirement_id
        )
        ON DELETE CASCADE,

    assessment_status TEXT NOT NULL,

    explanation TEXT,

    assessment_version TEXT NOT NULL,

    assessed_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    PRIMARY KEY (
        profile_id,
        eligibility_requirement_id,
        assessment_version
    ),

    CONSTRAINT valid_eligibility_assessment
        CHECK (
            assessment_status IN (
                'satisfied',
                'candidate',
                'not_satisfied',
                'needs_review'
            )
        )
);


CREATE TABLE IF NOT EXISTS job_profile_eligibility_summary (
    profile_id BIGINT NOT NULL
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    job_id BIGINT NOT NULL
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    assessment_version TEXT NOT NULL,

    total_requirements INTEGER NOT NULL,
    satisfied_requirements INTEGER NOT NULL,
    candidate_requirements INTEGER NOT NULL,
    not_satisfied_requirements INTEGER NOT NULL,
    needs_review_requirements INTEGER NOT NULL,

    assessed_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    PRIMARY KEY (
        profile_id,
        job_id,
        assessment_version
    )
);


CREATE INDEX IF NOT EXISTS
    idx_profile_eligibility_facts_profile
ON profile_eligibility_facts(profile_id);


CREATE INDEX IF NOT EXISTS
    idx_job_eligibility_requirement_mention
ON job_eligibility_requirements(
    requirement_mention_id
);


CREATE INDEX IF NOT EXISTS
    idx_job_profile_eligibility_job
ON job_profile_eligibility_summary(job_id);