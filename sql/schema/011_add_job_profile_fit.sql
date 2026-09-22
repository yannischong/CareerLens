CREATE TABLE IF NOT EXISTS job_profile_concept_fit (
    profile_id BIGINT NOT NULL
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    job_id BIGINT NOT NULL
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    concept_id BIGINT NOT NULL
        REFERENCES requirement_concepts(concept_id)
        ON DELETE CASCADE,

    requirement_type TEXT NOT NULL,

    requirement_level TEXT NOT NULL,

    claim_status TEXT NOT NULL,

    evidence_status TEXT NOT NULL,

    fit_status TEXT NOT NULL,

    fit_version TEXT NOT NULL,

    assessed_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    PRIMARY KEY (
        profile_id,
        job_id,
        concept_id,
        fit_version
    ),

    CONSTRAINT valid_fit_claim_status
        CHECK (
            claim_status IN (
                'confirmed',
                'candidate',
                'none'
            )
        ),

    CONSTRAINT valid_fit_evidence_status
        CHECK (
            evidence_status IN (
                'confirmed',
                'candidate',
                'none'
            )
        ),

    CONSTRAINT valid_fit_status
        CHECK (
            fit_status IN (
                'evidenced',
                'claimed_only',
                'candidate',
                'gap'
            )
        )
);


CREATE TABLE IF NOT EXISTS job_profile_requirement_checks (
    profile_id BIGINT NOT NULL
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    requirement_mention_id BIGINT NOT NULL
        REFERENCES job_requirement_mentions(
            requirement_mention_id
        )
        ON DELETE CASCADE,

    assessment_status TEXT NOT NULL,

    assessment_method TEXT NOT NULL,

    explanation TEXT,

    fit_version TEXT NOT NULL,

    assessed_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    PRIMARY KEY (
        profile_id,
        requirement_mention_id,
        fit_version
    ),

    CONSTRAINT valid_requirement_assessment
        CHECK (
            assessment_status IN (
                'needs_review',
                'satisfied',
                'partially_satisfied',
                'not_satisfied',
                'not_applicable'
            )
        )
);


CREATE TABLE IF NOT EXISTS job_profile_fit_summary (
    profile_id BIGINT NOT NULL
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    job_id BIGINT NOT NULL
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    fit_version TEXT NOT NULL,

    total_concepts INTEGER NOT NULL,

    required_concepts INTEGER NOT NULL,

    preferred_concepts INTEGER NOT NULL,

    unknown_level_concepts INTEGER NOT NULL,

    evidenced_concepts INTEGER NOT NULL,

    claimed_only_concepts INTEGER NOT NULL,

    candidate_concepts INTEGER NOT NULL,

    gap_concepts INTEGER NOT NULL,

    required_candidate_concepts INTEGER
        NOT NULL,

    required_gap_concepts INTEGER
        NOT NULL,

    unresolved_requirements INTEGER
        NOT NULL,

    assessed_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    PRIMARY KEY (
        profile_id,
        job_id,
        fit_version
    )
);


CREATE INDEX IF NOT EXISTS
    idx_job_profile_concept_fit_job
ON job_profile_concept_fit(job_id);


CREATE INDEX IF NOT EXISTS
    idx_job_profile_concept_fit_profile
ON job_profile_concept_fit(profile_id);


CREATE INDEX IF NOT EXISTS
    idx_job_profile_fit_summary_profile
ON job_profile_fit_summary(profile_id);