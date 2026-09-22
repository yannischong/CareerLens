-- 021_enforce_single_resume.sql
--
-- CareerCompass now supports exactly one current resume per profile.
--
-- Existing test accounts may contain multiple resume rows from the
-- previous multi-resume model. Keep the newest resume_id for each
-- profile and remove older rows. Existing foreign keys on resume data
-- handle their dependent rows; applications that referenced an older
-- resume become NULL via ON DELETE SET NULL.

WITH ranked_resumes AS (
    SELECT
        resume_id,
        ROW_NUMBER() OVER (
            PARTITION BY profile_id
            ORDER BY
                resume_id DESC
        ) AS resume_rank

    FROM resume_documents
)

DELETE FROM resume_documents rd

USING ranked_resumes ranked

WHERE
    rd.resume_id =
        ranked.resume_id

    AND
    ranked.resume_rank > 1;


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_resume_documents_one_per_profile

ON resume_documents (
    profile_id
);
