DROP POLICY IF EXISTS
    "Users upload own resumes"
ON storage.objects;


CREATE POLICY
    "Users upload own resumes"

ON storage.objects

FOR INSERT

TO authenticated

WITH CHECK (
    bucket_id = 'resumes'

    AND

    (storage.foldername(name))[1]
        = (SELECT auth.uid()::text)
);


DROP POLICY IF EXISTS
    "Users read own resumes"
ON storage.objects;


CREATE POLICY
    "Users read own resumes"

ON storage.objects

FOR SELECT

TO authenticated

USING (
    bucket_id = 'resumes'

    AND

    (storage.foldername(name))[1]
        = (SELECT auth.uid()::text)
);


DROP POLICY IF EXISTS
    "Users update own resumes"
ON storage.objects;


CREATE POLICY
    "Users update own resumes"

ON storage.objects

FOR UPDATE

TO authenticated

USING (
    bucket_id = 'resumes'

    AND

    (storage.foldername(name))[1]
        = (SELECT auth.uid()::text)
)

WITH CHECK (
    bucket_id = 'resumes'

    AND

    (storage.foldername(name))[1]
        = (SELECT auth.uid()::text)
);


DROP POLICY IF EXISTS
    "Users delete own resumes"
ON storage.objects;


CREATE POLICY
    "Users delete own resumes"

ON storage.objects

FOR DELETE

TO authenticated

USING (
    bucket_id = 'resumes'

    AND

    (storage.foldername(name))[1]
        = (SELECT auth.uid()::text)
);