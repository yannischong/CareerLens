ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS user_id UUID;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'user_profiles_user_id_unique'
    )
    THEN
        ALTER TABLE user_profiles
        ADD CONSTRAINT user_profiles_user_id_unique
        UNIQUE (user_id);
    END IF;
END
$$;