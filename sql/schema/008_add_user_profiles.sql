CREATE TABLE IF NOT EXISTS user_profiles (
    profile_id BIGSERIAL PRIMARY KEY,

    profile_name TEXT NOT NULL UNIQUE,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS resume_documents (
    resume_id BIGSERIAL PRIMARY KEY,

    profile_id BIGINT NOT NULL
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    original_filename TEXT NOT NULL,

    file_type TEXT NOT NULL,

    file_hash TEXT NOT NULL,

    raw_text TEXT NOT NULL,

    parser_version TEXT NOT NULL,

    uploaded_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    CONSTRAINT valid_resume_file_type
        CHECK (
            file_type IN (
                'pdf',
                'docx',
                'txt'
            )
        ),

    UNIQUE (
        profile_id,
        file_hash
    )
);


CREATE TABLE IF NOT EXISTS resume_sections (
    resume_section_id BIGSERIAL PRIMARY KEY,

    resume_id BIGINT NOT NULL
        REFERENCES resume_documents(resume_id)
        ON DELETE CASCADE,

    section_type TEXT NOT NULL,

    raw_heading TEXT,

    section_text TEXT NOT NULL,

    section_order INTEGER NOT NULL,

    extractor_version TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS profile_claims (
    claim_id BIGSERIAL PRIMARY KEY,

    profile_id BIGINT NOT NULL
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    resume_id BIGINT
        REFERENCES resume_documents(resume_id)
        ON DELETE CASCADE,

    claim_type TEXT NOT NULL,

    raw_text TEXT NOT NULL,

    normalized_text TEXT NOT NULL,

    claim_source TEXT NOT NULL
        DEFAULT 'resume',

    extractor_version TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS profile_evidence (
    evidence_id BIGSERIAL PRIMARY KEY,

    profile_id BIGINT NOT NULL
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    resume_id BIGINT
        REFERENCES resume_documents(resume_id)
        ON DELETE CASCADE,

    evidence_type TEXT NOT NULL,

    section_type TEXT,

    raw_text TEXT NOT NULL,

    normalized_text TEXT NOT NULL,

    evidence_source TEXT NOT NULL
        DEFAULT 'resume',

    extractor_version TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS
    idx_resume_documents_profile
ON resume_documents(profile_id);


CREATE INDEX IF NOT EXISTS
    idx_profile_claims_profile
ON profile_claims(profile_id);


CREATE INDEX IF NOT EXISTS
    idx_profile_evidence_profile
ON profile_evidence(profile_id);