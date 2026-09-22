DO $$

DECLARE
    table_record RECORD;

BEGIN

    FOR table_record IN

        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'

    LOOP

        EXECUTE format(
            'ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',
            table_record.tablename
        );

    END LOOP;

END

$$;


REVOKE ALL
ON ALL TABLES IN SCHEMA public
FROM anon, authenticated;


GRANT USAGE
ON SCHEMA public
TO authenticated;


GRANT SELECT, UPDATE
ON public.user_profiles
TO authenticated;


DROP POLICY IF EXISTS
    "Users can read own profile"
ON public.user_profiles;


CREATE POLICY
    "Users can read own profile"

ON public.user_profiles

FOR SELECT

TO authenticated

USING (
    auth.uid() IS NOT NULL
    AND
    (SELECT auth.uid()) = user_id
);


DROP POLICY IF EXISTS
    "Users can update own profile"
ON public.user_profiles;


CREATE POLICY
    "Users can update own profile"

ON public.user_profiles

FOR UPDATE

TO authenticated

USING (
    auth.uid() IS NOT NULL
    AND
    (SELECT auth.uid()) = user_id
)

WITH CHECK (
    auth.uid() IS NOT NULL
    AND
    (SELECT auth.uid()) = user_id
);