CREATE TABLE IF NOT EXISTS requirement_concepts (
    concept_id BIGSERIAL PRIMARY KEY,

    concept_type TEXT NOT NULL,

    canonical_name TEXT NOT NULL,

    normalized_key TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    UNIQUE (
        concept_type,
        normalized_key
    )
);


CREATE TABLE IF NOT EXISTS requirement_concept_aliases (
    alias_id BIGSERIAL PRIMARY KEY,

    concept_id BIGINT NOT NULL
        REFERENCES requirement_concepts(concept_id)
        ON DELETE CASCADE,

    alias_text TEXT NOT NULL,

    normalized_alias TEXT NOT NULL,

    alias_source TEXT NOT NULL
        DEFAULT 'observed',

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    UNIQUE (
        concept_id,
        normalized_alias
    )
);


CREATE TABLE IF NOT EXISTS job_requirement_concepts (
    requirement_mention_id BIGINT NOT NULL
        REFERENCES job_requirement_mentions(
            requirement_mention_id
        )
        ON DELETE CASCADE,

    concept_id BIGINT NOT NULL
        REFERENCES requirement_concepts(concept_id)
        ON DELETE CASCADE,

    raw_concept_text TEXT NOT NULL,

    extraction_method TEXT NOT NULL,

    confidence DOUBLE PRECISION,

    extractor_version TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    PRIMARY KEY (
        requirement_mention_id,
        concept_id,
        extractor_version
    )
);


CREATE TABLE IF NOT EXISTS concept_merge_candidates (
    concept_id_a BIGINT NOT NULL
        REFERENCES requirement_concepts(concept_id)
        ON DELETE CASCADE,

    concept_id_b BIGINT NOT NULL
        REFERENCES requirement_concepts(concept_id)
        ON DELETE CASCADE,

    similarity DOUBLE PRECISION NOT NULL,

    match_method TEXT NOT NULL,

    review_status TEXT NOT NULL
        DEFAULT 'unreviewed',

    detected_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    PRIMARY KEY (
        concept_id_a,
        concept_id_b
    ),

    CONSTRAINT ordered_concept_pair
        CHECK (
            concept_id_a <
            concept_id_b
        ),

    CONSTRAINT valid_concept_review_status
        CHECK (
            review_status IN (
                'unreviewed',
                'confirmed_same',
                'not_same'
            )
        )
);


CREATE INDEX IF NOT EXISTS
    idx_requirement_concepts_type
ON requirement_concepts(concept_type);


CREATE INDEX IF NOT EXISTS
    idx_job_requirement_concepts_concept
ON job_requirement_concepts(concept_id);