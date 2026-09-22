ALTER TABLE job_requirement_concepts
ADD COLUMN IF NOT EXISTS
    group_operator TEXT NOT NULL
    DEFAULT 'all_of';


ALTER TABLE job_requirement_concepts
ADD COLUMN IF NOT EXISTS
    group_is_open BOOLEAN NOT NULL
    DEFAULT FALSE;


DO $$
BEGIN
    ALTER TABLE job_requirement_concepts
    ADD CONSTRAINT
        valid_job_requirement_group_operator
    CHECK (
        group_operator IN (
            'all_of',
            'any_of'
        )
    );

EXCEPTION
    WHEN duplicate_object THEN
        NULL;
END
$$;


CREATE TABLE IF NOT EXISTS
    job_profile_requirement_group_fit (

        profile_id BIGINT NOT NULL
            REFERENCES user_profiles(
                profile_id
            )
            ON DELETE CASCADE,

        requirement_mention_id BIGINT NOT NULL
            REFERENCES job_requirement_mentions(
                requirement_mention_id
            )
            ON DELETE CASCADE,

        group_operator TEXT NOT NULL,

        group_is_open BOOLEAN NOT NULL
            DEFAULT FALSE,

        assessment_status TEXT NOT NULL,

        matched_concept_id BIGINT
            REFERENCES requirement_concepts(
                concept_id
            )
            ON DELETE SET NULL,

        assessment_method TEXT NOT NULL,

        explanation TEXT NOT NULL,

        fit_version TEXT NOT NULL,

        assessed_at TIMESTAMPTZ NOT NULL
            DEFAULT NOW(),

        PRIMARY KEY (
            profile_id,
            requirement_mention_id,
            fit_version
        ),

        CONSTRAINT
            valid_profile_group_operator
        CHECK (
            group_operator IN (
                'all_of',
                'any_of'
            )
        ),

        CONSTRAINT
            valid_profile_group_status
        CHECK (
            assessment_status IN (
                'evidenced',
                'claimed_only',
                'candidate',
                'gap',
                'needs_review'
            )
        )
    );


CREATE INDEX IF NOT EXISTS
    idx_profile_requirement_group_fit_profile
ON job_profile_requirement_group_fit(
    profile_id
);


CREATE INDEX IF NOT EXISTS
    idx_profile_requirement_group_fit_requirement
ON job_profile_requirement_group_fit(
    requirement_mention_id
);


ALTER TABLE job_profile_fit_summary
ADD COLUMN IF NOT EXISTS
    total_requirement_groups INTEGER
    NOT NULL DEFAULT 0;


ALTER TABLE job_profile_fit_summary
ADD COLUMN IF NOT EXISTS
    required_requirement_groups INTEGER
    NOT NULL DEFAULT 0;


ALTER TABLE job_profile_fit_summary
ADD COLUMN IF NOT EXISTS
    preferred_requirement_groups INTEGER
    NOT NULL DEFAULT 0;


ALTER TABLE job_profile_fit_summary
ADD COLUMN IF NOT EXISTS
    unknown_requirement_groups INTEGER
    NOT NULL DEFAULT 0;


ALTER TABLE job_profile_fit_summary
ADD COLUMN IF NOT EXISTS
    evidenced_requirement_groups INTEGER
    NOT NULL DEFAULT 0;


ALTER TABLE job_profile_fit_summary
ADD COLUMN IF NOT EXISTS
    claimed_only_requirement_groups INTEGER
    NOT NULL DEFAULT 0;


ALTER TABLE job_profile_fit_summary
ADD COLUMN IF NOT EXISTS
    candidate_requirement_groups INTEGER
    NOT NULL DEFAULT 0;


ALTER TABLE job_profile_fit_summary
ADD COLUMN IF NOT EXISTS
    gap_requirement_groups INTEGER
    NOT NULL DEFAULT 0;


ALTER TABLE job_profile_fit_summary
ADD COLUMN IF NOT EXISTS
    required_candidate_groups INTEGER
    NOT NULL DEFAULT 0;


ALTER TABLE job_profile_fit_summary
ADD COLUMN IF NOT EXISTS
    required_gap_groups INTEGER
    NOT NULL DEFAULT 0;