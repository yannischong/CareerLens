import argparse
import hashlib
import shutil

from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)
from src.user_profile.profile_extraction import (
    PROFILE_EXTRACTOR_VERSION,
    extract_profile_items,
)
from src.user_profile.resume_parser import (
    PARSER_VERSION,
    extract_resume_text,
)
from src.user_profile.sections import (
    SECTION_EXTRACTOR_VERSION,
    split_resume_sections,
)


load_dotenv()


def ingest_resume(
    profile_id,
    file_path,
    database_url=None,
    storage_path=None,
    keep_local_copy=False,
):
    engine = create_database_engine(
        database_url
    )

    source_path = Path(
        file_path
    ).expanduser().resolve()

    if not source_path.exists():
        raise FileNotFoundError(
            source_path
        )


    # Parse and extract everything before
    # replacing the current database row.
    #
    # If parsing/extraction fails, the
    # user's existing resume is untouched.
    file_bytes = (
        source_path.read_bytes()
    )

    file_hash = hashlib.sha256(
        file_bytes
    ).hexdigest()

    file_type, raw_text = (
        extract_resume_text(
            source_path
        )
    )

    sections = split_resume_sections(
        raw_text
    )

    claims, evidence = (
        extract_profile_items(
            sections
        )
    )


    if keep_local_copy:
        private_directory = Path(
            "data/private/resumes"
        )

        private_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        stored_filename = (
            f"{file_hash[:12]}"
            f"{source_path.suffix.lower()}"
        )

        local_stored_path = (
            private_directory
            / stored_filename
        )

        if not local_stored_path.exists():
            shutil.copy2(
                source_path,
                local_stored_path,
            )


    # The replacement itself is one
    # database transaction.
    #
    # DELETE + INSERT will either both
    # commit, or both roll back.
    with engine.begin() as connection:

        profile = (
            connection.execute(
                text(
                    """
                    SELECT
                        profile_id,
                        profile_name

                    FROM user_profiles

                    WHERE
                        profile_id =
                            :profile_id

                    FOR UPDATE;
                    """
                ),
                {
                    "profile_id":
                        profile_id,
                },
            )
            .mappings()
            .one_or_none()
        )


        if profile is None:
            raise ValueError(
                "Profile not found."
            )


        previous_rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        resume_id,
                        storage_path

                    FROM resume_documents

                    WHERE
                        profile_id =
                            :profile_id

                    ORDER BY
                        resume_id DESC;
                    """
                ),
                {
                    "profile_id":
                        profile_id,
                },
            )
            .mappings()
            .all()
        )


        previous_storage_paths = [
            row[
                "storage_path"
            ]

            for row
            in previous_rows

            if row[
                "storage_path"
            ]
        ]


        # Removing the resume cascades
        # its sections, claims and evidence.
        #
        # Applications use ON DELETE SET
        # NULL for historical resume_id.
        connection.execute(
            text(
                """
                DELETE FROM
                    resume_documents

                WHERE
                    profile_id =
                        :profile_id;
                """
            ),
            {
                "profile_id":
                    profile_id,
            },
        )


        resume_id = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        resume_documents (
                            profile_id,
                            original_filename,
                            file_type,
                            file_hash,
                            raw_text,
                            parser_version,
                            storage_path
                        )

                    VALUES (
                        :profile_id,
                        :original_filename,
                        :file_type,
                        :file_hash,
                        :raw_text,
                        :parser_version,
                        :storage_path
                    )

                    RETURNING resume_id;
                    """
                ),
                {
                    "profile_id":
                        profile_id,

                    "original_filename":
                        source_path.name,

                    "file_type":
                        file_type,

                    "file_hash":
                        file_hash,

                    "raw_text":
                        raw_text,

                    "parser_version":
                        PARSER_VERSION,

                    "storage_path":
                        storage_path,
                },
            )
            .scalar_one()
        )


        for section in sections:
            connection.execute(
                text(
                    """
                    INSERT INTO
                        resume_sections (
                            resume_id,
                            section_type,
                            raw_heading,
                            section_text,
                            section_order,
                            extractor_version
                        )

                    VALUES (
                        :resume_id,
                        :section_type,
                        :raw_heading,
                        :section_text,
                        :section_order,
                        :extractor_version
                    );
                    """
                ),
                {
                    "resume_id":
                        resume_id,

                    **section,

                    "extractor_version":
                        SECTION_EXTRACTOR_VERSION,
                },
            )


        for claim in claims:
            connection.execute(
                text(
                    """
                    INSERT INTO
                        profile_claims (
                            profile_id,
                            resume_id,
                            claim_type,
                            raw_text,
                            normalized_text,
                            extractor_version
                        )

                    VALUES (
                        :profile_id,
                        :resume_id,
                        :claim_type,
                        :raw_text,
                        :normalized_text,
                        :extractor_version
                    );
                    """
                ),
                {
                    "profile_id":
                        profile_id,

                    "resume_id":
                        resume_id,

                    **claim,

                    "extractor_version":
                        PROFILE_EXTRACTOR_VERSION,
                },
            )


        for item in evidence:
            connection.execute(
                text(
                    """
                    INSERT INTO
                        profile_evidence (
                            profile_id,
                            resume_id,
                            evidence_type,
                            section_type,
                            raw_text,
                            normalized_text,
                            extractor_version
                        )

                    VALUES (
                        :profile_id,
                        :resume_id,
                        :evidence_type,
                        :section_type,
                        :raw_text,
                        :normalized_text,
                        :extractor_version
                    );
                    """
                ),
                {
                    "profile_id":
                        profile_id,

                    "resume_id":
                        resume_id,

                    **item,

                    "extractor_version":
                        PROFILE_EXTRACTOR_VERSION,
                },
            )


    return {
        "profile_id":
            profile_id,

        "profile_name":
            profile[
                "profile_name"
            ],

        "resume_id":
            resume_id,

        "original_filename":
            source_path.name,

        "file_type":
            file_type,

        "file_hash":
            file_hash,

        "storage_path":
            storage_path,

        "replaced_resume":
            bool(
                previous_rows
            ),

        "previous_storage_paths":
            previous_storage_paths,

        "sections":
            len(
                sections
            ),

        "claims":
            len(
                claims
            ),

        "evidence":
            len(
                evidence
            ),
    }


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Import or replace the current "
            "CareerCompass resume."
        )
    )

    parser.add_argument(
        "--profile-id",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--file",
        required=True,
    )

    parser.add_argument(
        "--keep-local-copy",
        action="store_true",
    )

    args = parser.parse_args()

    result = ingest_resume(
        profile_id=
            args.profile_id,

        file_path=
            args.file,

        keep_local_copy=
            args.keep_local_copy,
    )

    print(
        f"Profile: "
        f"{result['profile_name']}"
    )

    print(
        f"Resume ID: "
        f"{result['resume_id']}"
    )

    print(
        f"Sections: "
        f"{result['sections']}"
    )

    print(
        f"Claims: "
        f"{result['claims']}"
    )

    print(
        f"Evidence items: "
        f"{result['evidence']}"
    )

    print(
        "Resume replacement complete."
    )
