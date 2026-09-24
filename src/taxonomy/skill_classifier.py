import re


WHITESPACE_PATTERN = re.compile(
    r"\s+"
)


def normalize_skill_text(
    text,
):
    text = (
        text
        .casefold()
        .replace(
            "&",
            " and ",
        )
    )

    text = re.sub(
        r"[^a-z0-9+#.]+",
        " ",
        text,
    )

    text = WHITESPACE_PATTERN.sub(
        " ",
        text,
    )

    return text.strip()


SOFT_SKILL_PATTERNS = {
    "Communication": [
        r"\bcommunication skills?\b",
        r"\bwritten and verbal communication\b",
        r"\bverbal and written communication\b",
        r"\bcommunicat(?:e|es|ing) effectively\b",
        r"\bcommunicat(?:e|es|ing) clearly\b",
        r"\barticulat(?:e|es|ing) complex\b",
        r"\bconvey complex\b",
    ],

    "Written Communication": [
        r"\bwritten communication\b",
        r"\bwriting skills?\b",
        r"\bwritten skills?\b",
        r"\bwrite clearly\b",
        r"\bwritten English\b",
    ],

    "Presentation": [
        r"\bpresentation skills?\b",
        r"\bpresent findings\b",
        r"\bpresent insights\b",
        r"\bpresent to (?:senior |key )?(?:management|leadership|stakeholders|clients)\b",
        r"\bdeliver presentations?\b",
        r"\bstorytell(?:ing)?\b",
    ],

    "Collaboration": [
        r"\bcollaborat(?:e|es|ed|ing|ion|ive)\b",
        r"\bteamwork\b",
        r"\bteam player\b",
        r"\bcross functional\b",
        r"\bwork across teams\b",
        r"\bwork effectively (?:with|across) teams\b",
        r"\bpartner with\b",
    ],

    "Stakeholder Management": [
        r"\bstakeholder management\b",
        r"\bstakeholder engagement\b",
        r"\bmanage stakeholders?\b",
        r"\bengage stakeholders?\b",
        r"\bsenior stakeholders?\b",
        r"\bbusiness stakeholders?\b",
    ],

    "Leadership": [
        r"\bleadership skills?\b",
        r"\bteam leadership\b",
        r"\blead teams?\b",
        r"\bleading teams?\b",
        r"\bpeople management\b",
        r"\bmentor(?:ing|ship)?\b",
        r"\bcoach(?:ing)? others\b",
    ],

    "Problem Solving": [
        r"\bproblem solving\b",
        r"\bproblem-solving\b",
        r"\bsolve (?:complex |business |technical )?problems?\b",
        r"\btroubleshoot(?:ing)?\b",
    ],

    "Analytical Thinking": [
        r"\banalytical skills?\b",
        r"\banalytical thinking\b",
        r"\banalytical mindset\b",
        r"\bstrong analytical\b",
        r"\banalytical capabilities\b",
    ],

    "Critical Thinking": [
        r"\bcritical thinking\b",
        r"\bcritical thinker\b",
        r"\bexercise sound judgement\b",
        r"\bsound judgment\b",
        r"\bsound judgement\b",
    ],

    "Attention to Detail": [
        r"\battention to detail\b",
        r"\bdetail oriented\b",
        r"\bdetail-oriented\b",
        r"\bmeticulous\b",
        r"\bhigh degree of accuracy\b",
    ],

    "Adaptability": [
        r"\badaptab(?:le|ility)\b",
        r"\bflexib(?:le|ility)\b",
        r"\bwork(?:ing)? in ambiguity\b",
        r"\bambiguous environment\b",
        r"\bfast paced environment\b",
        r"\bfast-paced environment\b",
        r"\bchanging priorities\b",
    ],

    "Time Management": [
        r"\btime management\b",
        r"\bmanage multiple deadlines\b",
        r"\bmeet tight deadlines\b",
        r"\bprioriti[sz](?:e|es|ing)\b",
        r"\bmultiple priorities\b",
    ],

    "Organisation": [
        r"\borganisational skills?\b",
        r"\borganizational skills?\b",
        r"\borganisation skills?\b",
        r"\borganization skills?\b",
        r"\bwell organised\b",
        r"\bwell organized\b",
    ],

    "Initiative": [
        r"\bself starter\b",
        r"\bself-starter\b",
        r"\bproactive\b",
        r"\btake initiative\b",
        r"\bshows? initiative\b",
    ],

    "Ownership": [
        r"\btake ownership\b",
        r"\bownership mindset\b",
        r"\baccountab(?:le|ility)\b",
        r"\bend to end ownership\b",
        r"\bend-to-end ownership\b",
    ],

    "Negotiation": [
        r"\bnegotiation skills?\b",
        r"\bnegotiate\b",
        r"\bnegotiating\b",
        r"\bpersuasion skills?\b",
        r"\binfluencing skills?\b",
    ],

    "Relationship Management": [
        r"\brelationship management\b",
        r"\brelationship building\b",
        r"\bbuild relationships\b",
        r"\bclient relationships?\b",
        r"\bpartner relationships?\b",
    ],

    "Interpersonal Skills": [
        r"\binterpersonal skills?\b",
        r"\bpeople skills?\b",
        r"\binterpersonal effectiveness\b",
    ],

    "Decision Making": [
        r"\bdecision making\b",
        r"\bdecision-making\b",
        r"\bmake sound decisions\b",
        r"\bmake informed decisions\b",
    ],

    "Creativity": [
        r"\bcreative thinking\b",
        r"\bcreative problem solving\b",
        r"\binnovative thinking\b",
        r"\bcreativity\b",
    ],

    "Customer Orientation": [
        r"\bcustomer focus(?:ed)?\b",
        r"\bcustomer centric\b",
        r"\bcustomer-centric\b",
        r"\bclient focus(?:ed)?\b",
        r"\bservice oriented\b",
        r"\bservice-oriented\b",
    ],
}


COMPILED_SOFT_SKILL_PATTERNS = {
    name: [
        re.compile(
            pattern,
            re.IGNORECASE,
        )
        for pattern in patterns
    ]
    for name, patterns
    in SOFT_SKILL_PATTERNS.items()
}


HARD_SKILL_ALIASES = {
    "microsoft excel": (
        "Excel",
        "excel",
    ),
    "ms excel": (
        "Excel",
        "excel",
    ),
    "excel": (
        "Excel",
        "excel",
    ),

    "microsoft power bi": (
        "Power BI",
        "power bi",
    ),
    "powerbi": (
        "Power BI",
        "power bi",
    ),
    "power bi": (
        "Power BI",
        "power bi",
    ),

    "microsoft powerpoint": (
        "PowerPoint",
        "powerpoint",
    ),
    "ms powerpoint": (
        "PowerPoint",
        "powerpoint",
    ),
    "power point": (
        "PowerPoint",
        "powerpoint",
    ),

    "financial modeling": (
        "Financial Modelling",
        "financial modelling",
    ),
    "financial modelling": (
        "Financial Modelling",
        "financial modelling",
    ),
    "financial models": (
        "Financial Modelling",
        "financial modelling",
    ),
    "financial model": (
        "Financial Modelling",
        "financial modelling",
    ),

    "discounted cash flow": (
        "Discounted Cash Flow (DCF)",
        "discounted cash flow",
    ),
    "dcf": (
        "Discounted Cash Flow (DCF)",
        "discounted cash flow",
    ),
    "dcf valuation": (
        "Discounted Cash Flow (DCF)",
        "discounted cash flow",
    ),
    "discounted cash flow valuation": (
        "Discounted Cash Flow (DCF)",
        "discounted cash flow",
    ),

    "financial statement analysis": (
        "Financial Statement Analysis",
        "financial statement analysis",
    ),
    "financial statements analysis": (
        "Financial Statement Analysis",
        "financial statement analysis",
    ),

    "mergers and acquisitions": (
        "Mergers & Acquisitions",
        "mergers and acquisitions",
    ),
    "m a": (
        "Mergers & Acquisitions",
        "mergers and acquisitions",
    ),

    "competitor analysis": (
        "Competitive Analysis",
        "competitive analysis",
    ),
    "competitive analysis": (
        "Competitive Analysis",
        "competitive analysis",
    ),

    "customer relationship management": (
        "Customer Relationship Management (CRM)",
        "customer relationship management",
    ),
    "crm": (
        "Customer Relationship Management (CRM)",
        "customer relationship management",
    ),

    "data visualization": (
        "Data Visualisation",
        "data visualisation",
    ),
    "data visualisation": (
        "Data Visualisation",
        "data visualisation",
    ),
}


LEADING_ACTION_PATTERN = re.compile(
    r"^(?:"
    r"build|"
    r"create|"
    r"develop|"
    r"prepare|"
    r"perform|"
    r"conduct|"
    r"execute|"
    r"undertake|"
    r"produce"
    r")\s+",
    re.IGNORECASE,
)


def find_soft_skills(
    text,
):
    normalized = normalize_skill_text(
        text
    )

    matches = []

    for (
        canonical_name,
        patterns,
    ) in (
        COMPILED_SOFT_SKILL_PATTERNS
        .items()
    ):
        canonical_key = (
            normalize_skill_text(
                canonical_name
            )
        )


        if normalized == canonical_key:
            matches.append(
                {
                    "raw_text":
                        canonical_name,

                    "normalized_key":
                        canonical_key,

                    "concept_type":
                        "soft_skill",

                    "confidence":
                        0.99,
                }
            )
            continue


        for pattern in patterns:

            if pattern.search(
                normalized
            ):
                matches.append(
                    {
                        "raw_text":
                            canonical_name,

                        "normalized_key":
                            normalize_skill_text(
                                canonical_name
                            ),

                        "concept_type":
                            "soft_skill",

                        "confidence":
                            0.98,
                    }
                )

                break

    return matches


def canonicalize_hard_skill(
    text,
):
    normalized = normalize_skill_text(
        text
    )

    canonical = (
        HARD_SKILL_ALIASES.get(
            normalized
        )
    )

    if canonical is not None:
        return canonical

    return (
        text,
        normalized,
    )


def get_hard_skill_aliases(
    normalized_key,
):
    normalized_key = (
        normalize_skill_text(
            normalized_key
        )
    )


    aliases = {
        alias

        for (
            alias,
            canonical,
        )
        in HARD_SKILL_ALIASES.items()

        if canonical[1]
        == normalized_key
    }


    return aliases


def reduce_action_phrase(
    text,
):
    reduced = (
        LEADING_ACTION_PATTERN.sub(
            "",
            text.strip(),
            count=1,
        )
        .strip()
    )

    return reduced or text.strip()
