DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'user_profiles_auth_user_fkey'
    )
    THEN
        ALTER TABLE public.user_profiles
        ADD CONSTRAINT user_profiles_auth_user_fkey
        FOREIGN KEY (user_id)
        REFERENCES auth.users(id)
        ON DELETE CASCADE;
    END IF;
END
$$;


CREATE OR REPLACE FUNCTION
    public.handle_new_careerlens_user()

RETURNS TRIGGER

LANGUAGE plpgsql

SECURITY DEFINER

SET search_path = ''

AS $$

BEGIN

    INSERT INTO public.user_profiles (
        user_id,
        profile_name
    )

    VALUES (
        NEW.id,

        COALESCE(
            NULLIF(
                NEW.raw_user_meta_data ->> 'full_name',
                ''
            ),

            split_part(
                COALESCE(
                    NEW.email,
                    'CareerLens User'
                ),
                '@',
                1
            )
        )
    )

    ON CONFLICT (user_id)
    DO NOTHING;

    RETURN NEW;

END;

$$;


DROP TRIGGER IF EXISTS
    on_auth_user_created
ON auth.users;


CREATE TRIGGER
    on_auth_user_created

AFTER INSERT
ON auth.users

FOR EACH ROW

EXECUTE FUNCTION
    public.handle_new_careerlens_user();