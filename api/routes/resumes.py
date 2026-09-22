import hashlib
import os
import tempfile

from pathlib import Path
from urllib.parse import quote

import requests

from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
)
from sqlalchemy import text

from api.auth import security
from api.profile import (
    CurrentProfile,
    get_current_profile,
)
from src.collection.database import (
    create_database_engine,
)
from src.eligibility.assess_eligibility import (
    assess_eligibility,
)
from src.eligibility.extract_job_eligibility import (
    extract_job_eligibility,
)
from src.eligibility.extract_profile_facts import (
    extract_profile_facts,
)
from src.matching.assess_fit import (
    assess_profile_fit,
)
from src.user_profile.ingest_resume import (
    ingest_resume,
)
from src.user_profile.map_profile_concepts import (
    map_profile_concepts,
)
from src.user_profile.resume_parser import (
    extract_resume_text,
)


load_dotenv()


router = APIRouter(
    prefix="/api/resumes",
    tags=["Resumes"],
)


SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)

SUPABASE_PUBLISHABLE_KEY = os.getenv(
    "SUPABASE_PUBLISHABLE_KEY"
)

DATABASE_URL = os.getenv(
    "SUPABASE_DATABASE_URL"
)


engine = create_database_engine(
    DATABASE_URL
)


MAX_RESUME_BYTES = (
    6 * 1024 * 1024
)


ALLOWED_FILE_TYPES = {
    ".pdf":
        "application/pdf",

    ".docx":
        (
            "application/vnd."
            "openxmlformats-officedocument."
            "wordprocessingml.document"
        ),

    ".txt":
        "text/plain",
}


def delete_storage_object(
    storage_path,
    access_token,
):
    if not storage_path:
        return True


    encoded_path = quote(
        storage_path,
        safe="/",
    )


    response = requests.delete(
        (
            f"{SUPABASE_URL.rstrip('/')}"
            f"/storage/v1/object/"
            f"resumes/"
            f"{encoded_path}"
        ),

        headers={
            "apikey":
                SUPABASE_PUBLISHABLE_KEY,

            "Authorization":
                (
                    "Bearer "
                    f"{access_token}"
                ),
        },

        timeout=
            30,
    )


    return (
        response.ok
        or response.status_code
        == 404
    )


def clear_stale_profile_analysis(
    profile_id,
):
    with engine.begin() as connection:

        # These tables are cached outputs
        # derived from the previous resume.
        connection.execute(
            text(
                """
                DELETE FROM
                    job_profile_concept_fit

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


        connection.execute(
            text(
                """
                DELETE FROM
                    job_profile_requirement_group_fit

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


        connection.execute(
            text(
                """
                DELETE FROM
                    job_profile_requirement_checks

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


        connection.execute(
            text(
                """
                DELETE FROM
                    job_profile_fit_summary

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


        connection.execute(
            text(
                """
                DELETE FROM
                    job_profile_eligibility_checks

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


        connection.execute(
            text(
                """
                DELETE FROM
                    job_profile_eligibility_summary

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


        # Preserve manually confirmed facts,
        # but remove facts derived from the
        # replaced resume before rebuilding.
        connection.execute(
            text(
                """
                DELETE FROM
                    profile_eligibility_facts

                WHERE
                    profile_id =
                        :profile_id

                    AND
                    source_type =
                        'resume';
                """
            ),
            {
                "profile_id":
                    profile_id,
            },
        )


@router.get("")
def list_resumes(
    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        rd.resume_id,
                        rd.original_filename,
                        rd.file_type,
                        rd.file_hash,
                        rd.parser_version,
                        rd.storage_path,
                        rd.uploaded_at,

                        (
                            SELECT COUNT(*)

                            FROM profile_claims pc

                            WHERE
                                pc.resume_id =
                                    rd.resume_id
                        ) AS claim_count,

                        (
                            SELECT COUNT(*)

                            FROM profile_evidence pe

                            WHERE
                                pe.resume_id =
                                    rd.resume_id
                        ) AS evidence_count

                    FROM resume_documents rd

                    WHERE
                        rd.profile_id =
                            :profile_id

                    ORDER BY
                        rd.resume_id DESC

                    LIMIT 1;
                    """
                ),
                {
                    "profile_id":
                        profile.profile_id,
                },
            )
            .mappings()
            .one_or_none()
        )


    resumes = (
        [
            dict(
                row
            )
        ]
        if row is not None
        else []
    )


    return {
        "count":
            len(
                resumes
            ),

        "resumes":
            resumes,

        "resume":
            (
                resumes[0]
                if resumes
                else None
            ),
    }


@router.post("")
def upload_resume(
    file: UploadFile = File(...),

    credentials:
        HTTPAuthorizationCredentials
        | None = Depends(
            security
        ),

    profile: CurrentProfile = Depends(
        get_current_profile
    ),
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Authentication required"
            ),
        )


    if (
        not SUPABASE_URL
        or not SUPABASE_PUBLISHABLE_KEY
        or not DATABASE_URL
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "Resume storage is "
                "not configured"
            ),
        )


    original_filename = (
        Path(
            file.filename
            or "resume"
        ).name
    )


    suffix = (
        Path(
            original_filename
        ).suffix.lower()
    )


    if suffix not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Supported resume formats: "
                "PDF, DOCX and TXT"
            ),
        )


    expected_content_type = (
        ALLOWED_FILE_TYPES[
            suffix
        ]
    )


    file_bytes = file.file.read(
        MAX_RESUME_BYTES + 1
    )


    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail=(
                "Resume file is empty"
            ),
        )


    if (
        len(
            file_bytes
        )
        > MAX_RESUME_BYTES
    ):
        raise HTTPException(
            status_code=413,
            detail=(
                "Resume must be "
                "6 MB or smaller"
            ),
        )


    file_hash = hashlib.sha256(
        file_bytes
    ).hexdigest()


    storage_path = (
        f"{profile.user_id}/"
        f"{file_hash[:24]}"
        f"{suffix}"
    )


    with tempfile.TemporaryDirectory() as temp_directory:

        temp_path = (
            Path(
                temp_directory
            )
            / original_filename
        )


        temp_path.write_bytes(
            file_bytes
        )


        # Validate and parse before touching
        # the user's current resume.
        try:
            extract_resume_text(
                temp_path
            )

        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=str(
                    exc
                ),
            ) from exc


        # Upload the new original first.
        #
        # The previous file is left intact
        # until the new DB resume has been
        # successfully created.
        storage_response = (
            requests.post(
                (
                    f"{SUPABASE_URL.rstrip('/')}"
                    f"/storage/v1/object/"
                    f"resumes/"
                    f"{storage_path}"
                ),

                headers={
                    "apikey":
                        SUPABASE_PUBLISHABLE_KEY,

                    "Authorization":
                        (
                            "Bearer "
                            f"{credentials.credentials}"
                        ),

                    "Content-Type":
                        expected_content_type,

                    "x-upsert":
                        "true",
                },

                data=
                    file_bytes,

                timeout=
                    30,
            )
        )


        if not storage_response.ok:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Failed to store "
                    "resume privately"
                ),
            )


        ingestion_result = None


        try:
            # 1. Atomically replace the
            #    database resume and all
            #    resume-derived claims/evidence.
            ingestion_result = (
                ingest_resume(
                    profile_id=
                        profile.profile_id,

                    file_path=
                        temp_path,

                    database_url=
                        DATABASE_URL,

                    storage_path=
                        storage_path,

                    keep_local_copy=
                        False,
                )
            )


            # 2. Clear cached fit/eligibility
            #    output from the old resume.
            clear_stale_profile_analysis(
                profile.profile_id
            )


            # 3. Rebuild profile concepts only
            #    from the new resume.
            mapping_result = (
                map_profile_concepts(
                    profile_id=
                        profile.profile_id,

                    database_url=
                        DATABASE_URL,
                )
            )


            # 4. Rebuild resume-derived
            #    eligibility facts.
            facts_result = (
                extract_profile_facts(
                    profile_id=
                        profile.profile_id,

                    database_url=
                        DATABASE_URL,
                )
            )


            # 5. Refresh the user's most
            #    recent provider search.
            with engine.connect() as connection:

                latest_search = (
                    connection.execute(
                        text(
                            """
                            SELECT
                                search_request_id

                            FROM
                                user_search_requests

                            WHERE
                                profile_id =
                                    :profile_id

                            ORDER BY
                                created_at DESC

                            LIMIT 1;
                            """
                        ),
                        {
                            "profile_id":
                                profile.profile_id,
                        },
                    )
                    .mappings()
                    .one_or_none()
                )


            latest_search_assessment = None


            if latest_search is not None:

                search_request_id = (
                    latest_search[
                        "search_request_id"
                    ]
                )


                eligibility_extraction = (
                    extract_job_eligibility(
                        database_url=
                            DATABASE_URL,

                        search_request_id=
                            search_request_id,
                    )
                )


                fit_result = (
                    assess_profile_fit(
                        profile_id=
                            profile.profile_id,

                        search_request_id=
                            search_request_id,

                        database_url=
                            DATABASE_URL,
                    )
                )


                eligibility_result = (
                    assess_eligibility(
                        profile_id=
                            profile.profile_id,

                        search_request_id=
                            search_request_id,

                        database_url=
                            DATABASE_URL,
                    )
                )


                latest_search_assessment = {
                    "search_request_id":
                        search_request_id,

                    "job_eligibility_extraction":
                        eligibility_extraction,

                    "profile_fit":
                        fit_result,

                    "eligibility":
                        eligibility_result,
                }


        except Exception as exc:

            # If ingestion never succeeded,
            # the old DB resume still exists.
            #
            # Remove the just-uploaded object
            # so a failed attempt does not
            # leave an orphan in Storage.
            if ingestion_result is None:

                delete_storage_object(
                    storage_path,
                    credentials.credentials,
                )


            raise HTTPException(
                status_code=500,
                detail=(
                    "Resume replacement "
                    "processing failed"
                ),
            ) from exc


    # The new resume is fully installed.
    # Remove previous private originals.
    storage_cleanup_failed = False


    for previous_path in (
        ingestion_result[
            "previous_storage_paths"
        ]
    ):

        if (
            previous_path
            == storage_path
        ):
            continue


        deleted = (
            delete_storage_object(
                previous_path,
                credentials.credentials,
            )
        )


        if not deleted:
            storage_cleanup_failed = True


    return {
        "replaced":
            ingestion_result[
                "replaced_resume"
            ],

        "resume": {
            "resume_id":
                ingestion_result[
                    "resume_id"
                ],

            "filename":
                original_filename,

            "file_type":
                ingestion_result[
                    "file_type"
                ],

            "storage_path":
                storage_path,

            "sections":
                ingestion_result[
                    "sections"
                ],

            "claims":
                ingestion_result[
                    "claims"
                ],

            "evidence":
                ingestion_result[
                    "evidence"
                ],
        },

        "concept_mapping": {
            "confirmed_claim_links":
                mapping_result[
                    "confirmed_claim_links"
                ],

            "candidate_claim_links":
                mapping_result[
                    "candidate_claim_links"
                ],

            "confirmed_evidence_links":
                mapping_result[
                    "confirmed_evidence_links"
                ],

            "candidate_evidence_links":
                mapping_result[
                    "candidate_evidence_links"
                ],
        },

        "profile_facts": {
            "created":
                facts_result[
                    "facts_created"
                ],
        },

        "latest_search_assessment":
            latest_search_assessment,

        "storage_cleanup_warning":
            storage_cleanup_failed,
    }
