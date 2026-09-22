CREATE TABLE IF NOT EXISTS profile_claim_concepts (
    claim_id BIGINT NOT NULL
        REFERENCES profile_claims(claim_id)
        ON DELETE CASCADE,

    concept_id BIGINT NOT NULL
        REFERENCES requirement_concepts(concept_id)
        ON DELETE CASCADE,

    match_method TEXT NOT NULL,

    similarity DOUBLE PRECISION,

    review_status TEXT NOT NULL,

    mapper_version TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    PRIMARY KEY (
        claim_id,
        concept_id,
        mapper_version
    ),

    CONSTRAINT valid_claim_concept_status
        CHECK (
            review_status IN (
                'confirmed',
                'candidate',
                'rejected'
            )
        )
);


CREATE TABLE IF NOT EXISTS profile_evidence_concepts (
    evidence_id BIGINT NOT NULL
        REFERENCES profile_evidence(evidence_id)
        ON DELETE CASCADE,

    concept_id BIGINT NOT NULL
        REFERENCES requirement_concepts(concept_id)
        ON DELETE CASCADE,

    match_method TEXT NOT NULL,

    similarity DOUBLE PRECISION,

    review_status TEXT NOT NULL,

    mapper_version TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    PRIMARY KEY (
        evidence_id,
        concept_id,
        mapper_version
    ),

    CONSTRAINT valid_evidence_concept_status
        CHECK (
            review_status IN (
                'confirmed',
                'candidate',
                'rejected'
            )
        )
);


CREATE INDEX IF NOT EXISTS
    idx_profile_claim_concepts_concept
ON profile_claim_concepts(concept_id);


CREATE INDEX IF NOT EXISTS
    idx_profile_evidence_concepts_concept
ON profile_evidence_concepts(concept_id);