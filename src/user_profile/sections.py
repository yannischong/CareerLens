import re


SECTION_EXTRACTOR_VERSION = (
    "resume_sections_v1"
)


HEADING_ALIASES = {
    "summary": {
        "summary",
        "profile",
        "professional summary",
        "professional profile",
        "about me",
    },

    "skills": {
        "skills",
        "technical skills",
        "core skills",
        "core competencies",
        "competencies",
        "technologies",
    },

    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "employment experience",
    },

    "projects": {
        "projects",
        "project experience",
        "selected projects",
        "academic projects",
        "personal projects",
    },

    "education": {
        "education",
        "academic background",
        "academic qualifications",
    },

    "certifications": {
        "certifications",
        "certificates",
        "professional certifications",
    },

    "licences": {
        "licences",
        "licenses",
    },

    "professional_registration": {
        "professional registration",
        "registrations",
    },

    "languages": {
        "languages",
        "language skills",
    },

    "awards": {
        "awards",
        "honours",
        "honors",
        "achievements",
    },

    "volunteering": {
        "volunteering",
        "volunteer experience",
    },
}


def normalize_heading(text):
    text = text.casefold().strip()

    text = re.sub(
        r"[^a-z ]",
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def identify_heading(line):
    normalized = normalize_heading(
        line
    )

    for section_type, aliases in (
        HEADING_ALIASES.items()
    ):
        if normalized in aliases:
            return section_type

    return None


def split_resume_sections(text):
    lines = [
        line.strip()
        for line in text.splitlines()
    ]

    sections = []

    current_type = "other"
    current_heading = None
    current_lines = []
    section_order = 1


    def save_current_section():
        nonlocal section_order

        section_text = "\n".join(
            current_lines
        ).strip()

        if not section_text:
            return

        sections.append(
            {
                "section_type":
                    current_type,

                "raw_heading":
                    current_heading,

                "section_text":
                    section_text,

                "section_order":
                    section_order,
            }
        )

        section_order += 1


    for line in lines:

        if not line:
            continue

        section_type = (
            identify_heading(line)
        )

        if section_type:

            save_current_section()

            current_type = (
                section_type
            )

            current_heading = line

            current_lines = []

        else:
            current_lines.append(line)


    save_current_section()

    return sections