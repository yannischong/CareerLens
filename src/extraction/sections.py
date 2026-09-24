from dataclasses import dataclass
import html
import re


WHITESPACE_PATTERN = re.compile(r"\s+")
HTML_BREAK_PATTERN = re.compile(
    r"<(?:br\s*/?|/p|/div|/li|/h[1-6])\s*>",
    re.IGNORECASE,
)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


SECTION_RULES = [
    (
        "preferred",
        re.compile(
            r"^(?:"
            r"preferred qualifications?|preferred experience|"
            r"preferred skills?|desirable qualifications?|"
            r"nice to have|nice-to-have|good to have|"
            r"bonus points?|bonus qualifications?|"
            r"additional qualifications?"
            r")$",
            re.IGNORECASE,
        ),
    ),
    (
        "requirements",
        re.compile(
            r"^(?:"
            r"requirements?|job requirements?|role requirements?|"
            r"qualifications?|minimum qualifications?|basic qualifications?|"
            r"essential qualifications?|mandatory requirements?|"
            r"skills(?: and| &) experience|experience(?: and| &) qualifications|"
            r"what (?:we(?:'re| are) looking for|you(?:'ll| will) need|you bring|you(?:'ll| will) bring)|"
            r"who you are|about you|your background|candidate profile|"
            r"what we need|you should have|must have|must-have|"
            r"success in this role requires|what makes you successful|"
            r"how you succeed|how you(?:'ll| will) succeed|what helps you succeed|"
            r"knowledge skills(?: and| &) abilities|technical skills|soft skills"
            r")$",
            re.IGNORECASE,
        ),
    ),
    (
        "responsibilities",
        re.compile(
            r"^(?:"
            r"responsibilities|key responsibilities|role responsibilities|"
            r"your responsibilities|what you(?:'ll| will) do|"
            r"what you(?:'ll| will) be doing|what you do|"
            r"your impact|key activities|key duties|duties|"
            r"day to day|day-to-day|what to expect"
            r")$",
            re.IGNORECASE,
        ),
    ),
    (
        "role",
        re.compile(
            r"^(?:"
            r"the role|about the role|role overview|job overview|"
            r"position overview|the opportunity|about the opportunity|"
            r"position summary|job summary|role summary|why join"
            r")$",
            re.IGNORECASE,
        ),
    ),
    (
        "company",
        re.compile(
            r"^(?:"
            r"about us|about the company|about our company|"
            r"who we are|our company|about the team|our team|"
            r"company overview|our mission|our values|"
            r"why we exist"
            r")$",
            re.IGNORECASE,
        ),
    ),
    (
        "benefits",
        re.compile(
            r"^(?:"
            r"benefits|benefits and perks|perks|perks and benefits|"
            r"what we offer|what you(?:'ll| will) get|"
            r"why join us|why you(?:'ll| will) love working here|"
            r"compensation and benefits|rewards and benefits"
            r")$",
            re.IGNORECASE,
        ),
    ),
    (
        "application",
        re.compile(
            r"^(?:"
            r"how to apply|application process|recruitment process|"
            r"hiring process|next steps|application instructions"
            r")$",
            re.IGNORECASE,
        ),
    ),
    (
        "legal",
        re.compile(
            r"^(?:"
            r"equal opportunity|equal opportunity employer|eeo|"
            r"diversity and inclusion|diversity inclusion(?: and| &) belonging|"
            r"privacy|privacy notice|data protection|"
            r"reasonable accommodation|accommodations?|"
            r"disclaimer|legal notice"
            r")$",
            re.IGNORECASE,
        ),
    ),
]


SECTION_WEIGHTS = {
    "requirements": {
        "hard_skill": 1.00,
        "soft_skill": 1.00,
        "general": 1.00,
    },
    "preferred": {
        "hard_skill": 0.90,
        "soft_skill": 0.90,
        "general": 0.90,
    },
    "responsibilities": {
        "hard_skill": 0.72,
        "soft_skill": 0.82,
        "general": 0.70,
    },
    "role": {
        "hard_skill": 0.62,
        "soft_skill": 0.72,
        "general": 0.60,
    },
    "other": {
        "hard_skill": 0.58,
        "soft_skill": 0.68,
        "general": 0.58,
    },
    "company": {
        "hard_skill": 0.05,
        "soft_skill": 0.05,
        "general": 0.05,
    },
    "benefits": {
        "hard_skill": 0.00,
        "soft_skill": 0.00,
        "general": 0.00,
    },
    "application": {
        "hard_skill": 0.00,
        "soft_skill": 0.00,
        "general": 0.00,
    },
    "legal": {
        "hard_skill": 0.00,
        "soft_skill": 0.00,
        "general": 0.00,
    },
}


IGNORED_SECTION_TYPES = {
    "company",
    "benefits",
    "application",
    "legal",
}


@dataclass(frozen=True)
class JobSection:
    section_type: str
    heading: str | None
    text: str

    @property
    def weights(self):
        return SECTION_WEIGHTS.get(
            self.section_type,
            SECTION_WEIGHTS["other"],
        )

    @property
    def is_ignored(self):
        return self.section_type in IGNORED_SECTION_TYPES

    def metadata(self):
        return {
            "section_type": self.section_type,
            "section_heading": self.heading,
            "section_hard_skill_weight": self.weights["hard_skill"],
            "section_soft_skill_weight": self.weights["soft_skill"],
            "section_general_weight": self.weights["general"],
        }


def _normalize_heading(text):
    text = html.unescape(text or "")
    text = text.strip().strip("#*-•●▪◦· ")
    text = re.sub(r"[:：]\s*$", "", text)
    text = WHITESPACE_PATTERN.sub(" ", text)
    return text.strip()


def classify_heading(text):
    heading = _normalize_heading(text)
    if not heading:
        return None

    # Headings should be compact. This prevents ordinary sentences such as
    # "Who we are looking for is..." from being interpreted as section titles.
    if len(heading) > 100 or len(heading.split()) > 14:
        return None

    for section_type, pattern in SECTION_RULES:
        if pattern.fullmatch(heading):
            return section_type

    return None



CANDIDATE_HEADING_HINT_PATTERN = re.compile(
    r"\b(?:"
    r"requirements?|qualifications?|skills?|competenc(?:y|ies)|"
    r"experience|background|candidate|profile|responsibilities|duties|"
    r"what .*bring|what .*need|looking for|successful|success"
    r")\b",
    re.IGNORECASE,
)


def looks_like_candidate_heading(text):
    heading = _normalize_heading(text)
    if not heading:
        return False

    if len(heading) > 100 or len(heading.split()) > 14:
        return False

    if heading.endswith((".", "!", "?")):
        return False

    return bool(
        CANDIDATE_HEADING_HINT_PATTERN.search(
            heading
        )
    )


def _default_section_type(source_field):
    if source_field in {
        "requirements_text",
        "education_requirements",
        "experience_requirements",
    }:
        return "requirements"

    return "other"


def _clean_source_text(text):
    text = html.unescape(text or "")
    text = HTML_BREAK_PATTERN.sub("\n", text)
    text = HTML_TAG_PATTERN.sub(" ", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Preserve physical line boundaries because they are valuable for section
    # detection, but collapse repeated spaces within each line.
    lines = []
    for raw_line in text.split("\n"):
        line = WHITESPACE_PATTERN.sub(" ", raw_line).strip()
        if line:
            lines.append(line)

    return lines


def split_job_sections(text, source_field=None):
    lines = _clean_source_text(text)
    if not lines:
        return []

    default_type = _default_section_type(source_field)
    sections = []
    current_type = default_type
    current_heading = None
    current_lines = []
    saw_heading = False

    def flush():
        nonlocal current_lines
        content = "\n".join(current_lines).strip()
        if content:
            sections.append(
                JobSection(
                    section_type=current_type,
                    heading=current_heading,
                    text=content,
                )
            )
        current_lines = []

    for line in lines:
        # Support headings written as "Requirements: Python, Excel...".
        inline_match = re.match(r"^([^:]{2,100}):\s*(.+)$", line)
        if inline_match:
            inline_type = classify_heading(inline_match.group(1))
            if inline_type is not None:
                flush()
                saw_heading = True
                current_type = inline_type
                current_heading = _normalize_heading(inline_match.group(1))
                current_lines = [inline_match.group(2).strip()]
                continue

        line_type = classify_heading(line)
        if line_type is not None:
            flush()
            saw_heading = True
            current_type = line_type
            current_heading = _normalize_heading(line)
            continue

        # A provider may use a candidate-oriented heading that is not yet in
        # the exact heading vocabulary. Never let an earlier ignored section
        # such as "About us" swallow the rest of the listing.
        if (
            current_type in IGNORED_SECTION_TYPES
            and looks_like_candidate_heading(line)
        ):
            flush()
            saw_heading = True
            current_type = "other"
            current_heading = _normalize_heading(line)
            continue

        current_lines.append(line)

    flush()

    if not saw_heading:
        return [
            JobSection(
                section_type=default_type,
                heading=None,
                text="\n".join(lines),
            )
        ]

    return sections


def infer_level_from_section(section_type, explicit_level):
    if explicit_level != "unknown":
        return explicit_level

    if section_type == "preferred":
        return "preferred"

    if section_type == "requirements":
        return "required"

    return "unknown"
