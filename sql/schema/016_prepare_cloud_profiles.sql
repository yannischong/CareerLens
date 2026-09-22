ALTER TABLE user_profiles
DROP CONSTRAINT IF EXISTS
    user_profiles_profile_name_key;


ALTER TABLE resume_documents
ADD COLUMN IF NOT EXISTS
    storage_path TEXT;