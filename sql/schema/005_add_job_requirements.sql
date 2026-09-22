CREATE TABLE IF NOT EXISTS job_requirement_mentions (
    requirement_mention_id BIGSERIAL PRIMARY KEY,

    job_id BIGINT NOT NULL
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    source_field TEXT NOT NULL,

    requirement_type TEXT NOT NULL,

    requirement_level TEXT NOT NULL
        DEFAULT 'unknown',

    raw_text TEXT NOT NULL,

    normalized_text TEXT NOT NULL,

    structured_value JSONB NOT NULL
        DEFAULT '{}'::JSONB,

    rule_name TEXT NOT NULL,

    extractor_version TEXT NOT NULL,

    extracted_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    CONSTRAINT valid_requirement_type
        CHECK (
            requirement_type IN (
                'experience',
                'education',
                'skill',
                'certification',
                'language',
                'work_authorization',
                'availability',
                'other'
            )
        ),

    CONSTRAINT valid_requirement_level
        CHECK (
            requirement_level IN (
                'required',
                'preferred',
                'unknown'
            )
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_job_requirement_mentions
ON job_requirement_mentions (
    job_id,
    source_field,
    requirement_type,
    normalized_text,
    extractor_version
);


CREATE INDEX IF NOT EXISTS
    idx_job_requirement_mentions_job
ON job_requirement_mentions(job_id);


CREATE INDEX IF NOT EXISTS
    idx_job_requirement_mentions_type
ON job_requirement_mentions(requirement_type);