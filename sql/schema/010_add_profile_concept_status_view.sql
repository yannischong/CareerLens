CREATE OR REPLACE VIEW profile_concept_status AS

WITH profile_concept_pairs AS (

    SELECT
        pc.profile_id,
        pcc.concept_id,
        pcc.mapper_version

    FROM profile_claim_concepts pcc

    JOIN profile_claims pc
        ON pcc.claim_id = pc.claim_id

    UNION

    SELECT
        pe.profile_id,
        pec.concept_id,
        pec.mapper_version

    FROM profile_evidence_concepts pec

    JOIN profile_evidence pe
        ON pec.evidence_id = pe.evidence_id
)

SELECT
    pair.profile_id,
    pair.concept_id,
    pair.mapper_version,

    c.concept_type,
    c.canonical_name,

    CASE
        WHEN EXISTS (
            SELECT 1
            FROM profile_claim_concepts pcc
            JOIN profile_claims pc
                ON pcc.claim_id = pc.claim_id

            WHERE
                pc.profile_id = pair.profile_id
                AND pcc.concept_id = pair.concept_id
                AND pcc.mapper_version =
                    pair.mapper_version
                AND pcc.review_status =
                    'confirmed'
        )
        THEN 'confirmed'

        WHEN EXISTS (
            SELECT 1
            FROM profile_claim_concepts pcc
            JOIN profile_claims pc
                ON pcc.claim_id = pc.claim_id

            WHERE
                pc.profile_id = pair.profile_id
                AND pcc.concept_id = pair.concept_id
                AND pcc.mapper_version =
                    pair.mapper_version
                AND pcc.review_status =
                    'candidate'
        )
        THEN 'candidate'

        ELSE 'none'
    END AS claim_status,


    CASE
        WHEN EXISTS (
            SELECT 1
            FROM profile_evidence_concepts pec
            JOIN profile_evidence pe
                ON pec.evidence_id = pe.evidence_id

            WHERE
                pe.profile_id = pair.profile_id
                AND pec.concept_id = pair.concept_id
                AND pec.mapper_version =
                    pair.mapper_version
                AND pec.review_status =
                    'confirmed'
        )
        THEN 'confirmed'

        WHEN EXISTS (
            SELECT 1
            FROM profile_evidence_concepts pec
            JOIN profile_evidence pe
                ON pec.evidence_id = pe.evidence_id

            WHERE
                pe.profile_id = pair.profile_id
                AND pec.concept_id = pair.concept_id
                AND pec.mapper_version =
                    pair.mapper_version
                AND pec.review_status =
                    'candidate'
        )
        THEN 'candidate'

        ELSE 'none'
    END AS evidence_status

FROM profile_concept_pairs pair

JOIN requirement_concepts c
    ON pair.concept_id = c.concept_id;