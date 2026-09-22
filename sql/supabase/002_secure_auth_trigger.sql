CREATE SCHEMA IF NOT EXISTS private;


CREATE OR REPLACE FUNCTION
    private.handle_new_careerlens_user()

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
    private.handle_new_careerlens_user();


DROP FUNCTION IF EXISTS
    public.handle_new_careerlens_user();


REVOKE ALL
ON SCHEMA private
FROM PUBLIC, anon, authenticated;


REVOKE ALL
ON FUNCTION private.handle_new_careerlens_user()
FROM PUBLIC, anon, authenticated;