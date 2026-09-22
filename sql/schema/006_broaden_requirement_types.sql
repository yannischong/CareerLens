ALTER TABLE job_requirement_mentions
DROP CONSTRAINT IF EXISTS valid_requirement_type;


ALTER TABLE job_requirement_mentions
ADD CONSTRAINT valid_requirement_type
CHECK (
    requirement_type IN (
        'experience',
        'education',
        'skill',
        'tool',
        'certification',
        'licence',
        'professional_registration',
        'language',
        'domain_knowledge',
        'work_authorization',
        'availability',
        'physical_requirement',
        'security_clearance',
        'other'
    )
);