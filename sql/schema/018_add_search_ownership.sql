CREATE TABLE IF NOT EXISTS user_search_requests (
    search_request_id BIGINT PRIMARY KEY
        REFERENCES search_requests(search_request_id)
        ON DELETE CASCADE,

    profile_id BIGINT NOT NULL
        REFERENCES user_profiles(profile_id)
        ON DELETE CASCADE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS
    idx_user_search_requests_profile_id
ON user_search_requests(profile_id);


ALTER TABLE public.user_search_requests
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
        ON public.user_search_requests
        FROM anon;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'authenticated'
    )
    THEN
        REVOKE ALL
        ON public.user_search_requests
        FROM authenticated;
    END IF;

END
$$;