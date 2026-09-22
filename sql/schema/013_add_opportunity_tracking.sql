CREATE TABLE IF NOT EXISTS opportunities (
    opportunity_id BIGSERIAL PRIMARY KEY,

    profile_id BIGINT NOT NULL
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    job_id BIGINT NOT NULL
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    source_search_request_id BIGINT
        REFERENCES search_requests(search_request_id)
        ON DELETE SET NULL,

    current_status TEXT NOT NULL
        DEFAULT 'discovered',

    priority TEXT NOT NULL
        DEFAULT 'medium',

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    CONSTRAINT valid_opportunity_status
        CHECK (
            current_status IN (
                'discovered',
                'saved',
                'to_apply',
                'applied',
                'oa',
                'interview',
                'offer',
                'rejected',
                'withdrawn',
                'closed'
            )
        ),

    CONSTRAINT valid_opportunity_priority
        CHECK (
            priority IN (
                'low',
                'medium',
                'high'
            )
        ),

    UNIQUE (
        profile_id,
        job_id
    )
);


CREATE TABLE IF NOT EXISTS opportunity_events (
    event_id BIGSERIAL PRIMARY KEY,

    opportunity_id BIGINT NOT NULL
        REFERENCES opportunities(opportunity_id)
        ON DELETE CASCADE,

    event_type TEXT NOT NULL,

    from_status TEXT,
    to_status TEXT,

    event_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    notes TEXT,

    metadata JSONB NOT NULL
        DEFAULT '{}'::JSONB,

    event_source TEXT NOT NULL
        DEFAULT 'manual',

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    CONSTRAINT valid_event_type
        CHECK (
            event_type IN (
                'created',
                'status_change',
                'note',
                'deadline',
                'oa',
                'interview',
                'follow_up',
                'offer',
                'rejection',
                'withdrawal',
                'other'
            )
        )
);


CREATE TABLE IF NOT EXISTS applications (
    application_id BIGSERIAL PRIMARY KEY,

    opportunity_id BIGINT NOT NULL UNIQUE
        REFERENCES opportunities(opportunity_id)
        ON DELETE CASCADE,

    resume_id BIGINT
        REFERENCES resume_documents(resume_id)
        ON DELETE SET NULL,

    application_url TEXT,

    application_method TEXT,

    submitted_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    referral_used BOOLEAN NOT NULL
        DEFAULT FALSE,

    cover_letter_used BOOLEAN NOT NULL
        DEFAULT FALSE,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS
    idx_opportunities_profile
ON opportunities(profile_id);


CREATE INDEX IF NOT EXISTS
    idx_opportunities_status
ON opportunities(
    profile_id,
    current_status
);


CREATE INDEX IF NOT EXISTS
    idx_opportunity_events_opportunity
ON opportunity_events(
    opportunity_id,
    event_at
);


CREATE INDEX IF NOT EXISTS
    idx_applications_submitted
ON applications(submitted_at);