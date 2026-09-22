CREATE TABLE IF NOT EXISTS user_search_quota (
    profile_id BIGINT PRIMARY KEY
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    searches_used INTEGER NOT NULL DEFAULT 0
        CHECK (
            searches_used >= 0
            AND searches_used <= 2
        ),

    last_search_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


ALTER TABLE public.user_search_quota
ENABLE ROW LEVEL SECURITY;


DO $$
BEGIN

    IF EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'anon'
    )
    THEN
        REVOKE ALL
        ON public.user_search_quota
        FROM anon;
    END IF;


    IF EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'authenticated'
    )
    THEN
        REVOKE ALL
        ON public.user_search_quota
        FROM authenticated;
    END IF;

END
$$;