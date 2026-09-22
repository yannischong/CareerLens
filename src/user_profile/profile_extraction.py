import html
import re


PROFILE_EXTRACTOR_VERSION = (
    "profile_v2"
)


CLAIM_SECTIONS = {
    "skills",
    "languages",
}


EVIDENCE_SECTION_TYPES = {
    "experience":
        "experience",

    "projects":
        "project",

    "education":
        "education",

    "certifications":
        "certification",

    "licences":
        "licence",

    "professional_registration":
        "professional_registration",

    "awards":
        "other",

    "volunteering":
        "other",
}


WHITESPACE_PATTERN = re.compile(
    r"\s+"
)


CLAIM_SPLIT_PATTERN = re.compile(
    r"[,;|\t]"
    r"|\s+/\s+"
)


BULLET_PATTERN = re.compile(
    r"[•●▪◦]+"
)


def normalize_profile_text(
    text,
):
    text = html.unescape(
        text
    )

    text = text.casefold()

    text = WHITESPACE_PATTERN.sub(
        " ",
        text,
    )

    return text.strip()


def clean_profile_item(
    text,
):
    text = html.unescape(
        text
    )

    text = text.strip(
        " \t\r\n"
        "•●▪◦"
        "-–—"
        ":;"
    )

    text = WHITESPACE_PATTERN.sub(
        " ",
        text,
    )

    return text.strip()


def split_claims(
    text,
):
    claims = []


    text = BULLET_PATTERN.sub(
        ",",
        text,
    )


    for line in text.splitlines():

        line = clean_profile_item(
            line
        )


        if not line:
            continue


        parts = CLAIM_SPLIT_PATTERN.split(
            line
        )


        for part in parts:

            part = clean_profile_item(
                part
            )


            if not part:
                continue


            claims.append(
                part
            )


    return claims


def split_evidence(
    text,
):
    evidence = []


    for raw_line in text.splitlines():

        fragments = BULLET_PATTERN.split(
            raw_line
        )


        for fragment in fragments:

            fragment = clean_profile_item(
                fragment
            )


            if not fragment:
                continue


            # Keep short but meaningful
            # evidence such as:
            #
            # Dean's List
            # AWS Certified...
            #
            # Single-word noise is
            # discarded.
            if len(
                fragment.split()
            ) < 2:
                continue


            evidence.append(
                fragment
            )


    return evidence


def extract_profile_items(
    sections,
):
    claims = []
    evidence = []


    seen_claims = set()
    seen_evidence = set()


    for section in sections:

        section_type = (
            section[
                "section_type"
            ]
        )

        section_text = (
            section[
                "section_text"
            ]
        )


        if (
            section_type
            in CLAIM_SECTIONS
        ):

            for claim in split_claims(
                section_text
            ):

                normalized = (
                    normalize_profile_text(
                        claim
                    )
                )


                key = (
                    section_type,
                    normalized,
                )


                if key in seen_claims:
                    continue


                seen_claims.add(
                    key
                )


                claims.append(
                    {
                        "claim_type":
                            section_type,

                        "raw_text":
                            claim,

                        "normalized_text":
                            normalized,
                    }
                )


        evidence_type = (
            EVIDENCE_SECTION_TYPES.get(
                section_type
            )
        )


        if evidence_type:

            for item in split_evidence(
                section_text
            ):

                normalized = (
                    normalize_profile_text(
                        item
                    )
                )


                key = (
                    evidence_type,
                    normalized,
                )


                if key in seen_evidence:
                    continue


                seen_evidence.add(
                    key
                )


                evidence.append(
                    {
                        "evidence_type":
                            evidence_type,

                        "section_type":
                            section_type,

                        "raw_text":
                            item,

                        "normalized_text":
                            normalized,
                    }
                )


    return (
        claims,
        evidence,
    )