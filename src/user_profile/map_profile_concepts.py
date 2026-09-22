import argparse
import re

from functools import lru_cache

from dotenv import load_dotenv
from sentence_transformers import (
    SentenceTransformer,
)
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)
from src.taxonomy.atomic import (
    normalize_concept,
)


MAPPER_VERSION = (
    "profile_concepts_v2"
)

CONCEPT_VERSION = (
    "atomic_concepts_v2"
)


MODEL_NAME = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)


CLAIM_SIMILARITY_THRESHOLD = (
    0.70
)

EVIDENCE_SIMILARITY_THRESHOLD = (
    0.65
)


MAX_SEMANTIC_CANDIDATES = 3


SKILL_LIKE_TYPES = {
    "skill",
    "tool",
    "domain_knowledge",
}


CLAIM_ALLOWED_TYPES = {
    "skills":
        SKILL_LIKE_TYPES,

    "languages": {
        "language",
    },
}


EVIDENCE_ALLOWED_TYPES = {
    "experience":
        SKILL_LIKE_TYPES,

    "project":
        SKILL_LIKE_TYPES,

    "education": {
        "education",
    },

    "certification": {
        "certification",
    },

    "licence": {
        "licence",
    },

    "professional_registration": {
        "professional_registration",
    },

    "other":
        SKILL_LIKE_TYPES,
}


SPELLING_VARIANTS = {
    "visualisation":
        "visualization",

    "visualization":
        "visualisation",

    "optimisation":
        "optimization",

    "optimization":
        "optimisation",

    "organisation":
        "organization",

    "organization":
        "organisation",

    "analyse":
        "analyze",

    "analyze":
        "analyse",
}


# These represent sufficiently strong
# equivalences to count as confirmed
# lexical matches.
CONFIRMED_CONCEPT_ALIASES = {
    "data cleansing": {
        "data cleaning",
    },

    "amazon bedrock": {
        "aws bedrock",
    },
}


# These are related enough to surface
# as candidates, but are not treated
# as proof of the exact requirement.
CANDIDATE_CONCEPT_ALIASES = {
    "analyze data": {
        "statistical analysis",
        "data analysis",
    },

    "ai application development": {
        "agentic ai",
        "agentic ai system",
        "agentic ai platform",
    },
}


load_dotenv()


@lru_cache(
    maxsize=1
)
def get_model():
    return SentenceTransformer(
        MODEL_NAME
    )


def contains_alias(
    normalized_text,
    normalized_alias,
):
    if not normalized_alias:
        return False


    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(
            normalized_alias
        )
        + r"(?![a-z0-9])"
    )


    return bool(
        re.search(
            pattern,
            normalized_text,
        )
    )


def get_confirmed_aliases(
    normalized_key,
):
    aliases = set(
        CONFIRMED_CONCEPT_ALIASES.get(
            normalized_key,
            set(),
        )
    )


    # The current requirement extractor
    # can produce keys such as:
    #
    # large language models llms
    #
    # Explicit LLM terminology in a
    # resume is strong evidence of the
    # same concept.
    if normalized_key.startswith(
        "large language models"
    ):
        aliases.update(
            {
                "large language model",
                "large language models",
                "llm",
                "llms",
                "llm engineering",
                "llm orchestration",
            }
        )


    return aliases


def get_candidate_aliases(
    normalized_key,
):
    return set(
        CANDIDATE_CONCEPT_ALIASES.get(
            normalized_key,
            set(),
        )
    )


def expand_alias(
    alias,
):
    alias = normalize_concept(
        alias
    )


    if not alias:
        return set()


    variants = {
        alias
    }


    for (
        source,
        target,
    ) in SPELLING_VARIANTS.items():

        if source in alias:

            variants.add(
                alias.replace(
                    source,
                    target,
                )
            )


    if alias.startswith(
        "microsoft "
    ):

        variants.add(
            alias.removeprefix(
                "microsoft "
            )
        )


    if alias == "excel":

        variants.update(
            {
                "microsoft excel",
                "ms excel",
            }
        )


    if alias == "power bi":

        variants.update(
            {
                "powerbi",
                "microsoft power bi",
            }
        )


    if alias == "power automate":

        variants.update(
            {
                "microsoft power automate",
            }
        )


    return variants


def semantic_fragments(
    raw_text,
):
    raw_text = re.sub(
        r"\s+",
        " ",
        raw_text,
    ).strip()


    fragments = [
        raw_text
    ]


    coarse_parts = re.split(
        r"[.;|•●▪]+",
        raw_text,
    )


    for part in coarse_parts:

        part = part.strip(
            " ,:-"
        )


        if (
            len(
                part.split()
            )
            >= 3
        ):
            fragments.append(
                part
            )


        comma_parts = re.split(
            r"\s*,\s*",
            part,
        )


        for comma_part in comma_parts:

            comma_part = (
                comma_part.strip(
                    " ,:-"
                )
            )


            if (
                len(
                    comma_part.split()
                )
                >= 3
            ):
                fragments.append(
                    comma_part
                )


        and_parts = re.split(
            r"\s+\band\b\s+",
            part,
            flags=re.IGNORECASE,
        )


        if len(and_parts) > 1:

            for and_part in and_parts:

                and_part = (
                    and_part.strip(
                        " ,:-"
                    )
                )


                if (
                    len(
                        and_part.split()
                    )
                    >= 3
                ):
                    fragments.append(
                        and_part
                    )


    unique = []
    seen = set()


    for fragment in fragments:

        normalized = (
            normalize_concept(
                fragment
            )
        )


        if not normalized:
            continue


        if normalized in seen:
            continue


        seen.add(
            normalized
        )

        unique.append(
            fragment
        )


    return unique


def allowed_concept_indexes(
    concepts,
    allowed_types,
):
    return [
        index

        for index, concept
        in enumerate(
            concepts
        )

        if (
            concept[
                "concept_type"
            ]
            in allowed_types
        )
    ]


def direct_matches(
    raw_text,
    concepts,
    aliases_by_concept,
    allowed_types,
):
    normalized_text = (
        normalize_concept(
            raw_text
        )
    )


    matches = set()


    for concept in concepts:

        if (
            concept[
                "concept_type"
            ]
            not in allowed_types
        ):
            continue


        concept_id = (
            concept[
                "concept_id"
            ]
        )


        for alias in (
            aliases_by_concept[
                concept_id
            ]
        ):

            if (
                normalized_text
                == alias

                or

                contains_alias(
                    normalized_text,
                    alias,
                )
            ):

                matches.add(
                    concept_id
                )

                break


    return matches


def curated_candidate_matches(
    raw_text,
    concepts,
    allowed_types,
    excluded_ids,
):
    normalized_text = (
        normalize_concept(
            raw_text
        )
    )


    matches = set()


    for concept in concepts:

        concept_id = (
            concept[
                "concept_id"
            ]
        )


        if concept_id in excluded_ids:
            continue


        if (
            concept[
                "concept_type"
            ]
            not in allowed_types
        ):
            continue


        normalized_key = (
            concept[
                "normalized_key"
            ]
        )


        aliases = (
            get_candidate_aliases(
                normalized_key
            )
        )


        for alias in aliases:

            normalized_alias = (
                normalize_concept(
                    alias
                )
            )


            if (
                normalized_text
                == normalized_alias

                or

                contains_alias(
                    normalized_text,
                    normalized_alias,
                )
            ):

                matches.add(
                    concept_id
                )

                break


    return matches


def semantic_candidates(
    raw_text,
    concepts,
    concept_embeddings,
    eligible_indexes,
    excluded_ids,
    threshold,
    model,
):
    fragments = semantic_fragments(
        raw_text
    )


    if not fragments:
        return []


    fragment_embeddings = (
        model.encode(
            fragments,
            normalize_embeddings=True,
        )
    )


    score_matrix = (
        concept_embeddings
        @
        fragment_embeddings.T
    )


    scores = (
        score_matrix.max(
            axis=1
        )
    )


    ranked_indexes = sorted(
        eligible_indexes,

        key=lambda index:
            float(
                scores[index]
            ),

        reverse=True,
    )


    candidates = []


    for index in ranked_indexes:

        concept = (
            concepts[index]
        )


        concept_id = (
            concept[
                "concept_id"
            ]
        )


        if concept_id in excluded_ids:
            continue


        normalized_key = (
            concept[
                "normalized_key"
            ]
        )


        # Very short concepts such as
        # R or C should only be matched
        # through explicit lexical
        # evidence.
        if len(
            normalized_key
        ) <= 2:
            continue


        similarity = float(
            scores[index]
        )


        if similarity < threshold:
            break


        candidates.append(
            (
                concept_id,
                similarity,
            )
        )


        if (
            len(candidates)
            >=
            MAX_SEMANTIC_CANDIDATES
        ):
            break


    return candidates


def map_profile_concepts(
    profile_id,
    database_url=None,
):
    engine = create_database_engine(
        database_url
    )


    with engine.connect() as connection:

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
                            :profile_id;
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


        concepts = (
            connection.execute(
                text(
                    """
                    SELECT DISTINCT
                        c.concept_id,
                        c.concept_type,
                        c.canonical_name,
                        c.normalized_key

                    FROM
                        requirement_concepts c

                    JOIN
                        job_requirement_concepts jrc

                        ON
                            jrc.concept_id =
                            c.concept_id

                    WHERE
                        jrc.extractor_version =
                            :concept_version

                    ORDER BY
                        c.concept_id;
                    """
                ),
                {
                    "concept_version":
                        CONCEPT_VERSION,
                },
            )
            .mappings()
            .all()
        )


        aliases = (
            connection.execute(
                text(
                    """
                    SELECT
                        a.concept_id,
                        a.normalized_alias

                    FROM
                        requirement_concept_aliases a

                    JOIN
                        job_requirement_concepts jrc

                        ON
                            jrc.concept_id =
                            a.concept_id

                    WHERE
                        jrc.extractor_version =
                            :concept_version

                    GROUP BY
                        a.concept_id,
                        a.normalized_alias

                    ORDER BY
                        a.concept_id,
                        a.normalized_alias;
                    """
                ),
                {
                    "concept_version":
                        CONCEPT_VERSION,
                },
            )
            .mappings()
            .all()
        )


        claims = (
            connection.execute(
                text(
                    """
                    SELECT
                        claim_id,
                        claim_type,
                        raw_text

                    FROM profile_claims

                    WHERE
                        profile_id =
                            :profile_id

                    ORDER BY
                        claim_id;
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


        evidence = (
            connection.execute(
                text(
                    """
                    SELECT
                        evidence_id,
                        evidence_type,
                        raw_text

                    FROM profile_evidence

                    WHERE
                        profile_id =
                            :profile_id

                    ORDER BY
                        evidence_id;
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


    aliases_by_concept = {
        concept[
            "concept_id"
        ]: expand_alias(
            concept[
                "normalized_key"
            ]
        )

        for concept in concepts
    }


    for concept in concepts:

        concept_id = (
            concept[
                "concept_id"
            ]
        )

        normalized_key = (
            concept[
                "normalized_key"
            ]
        )


        for alias in (
            get_confirmed_aliases(
                normalized_key
            )
        ):

            aliases_by_concept[
                concept_id
            ].update(
                expand_alias(
                    alias
                )
            )


    for alias in aliases:

        concept_id = (
            alias[
                "concept_id"
            ]
        )


        if (
            concept_id
            not in aliases_by_concept
        ):
            continue


        aliases_by_concept[
            concept_id
        ].update(
            expand_alias(
                alias[
                    "normalized_alias"
                ]
            )
        )


    # Remove previous mapping output for
    # this profile before rebuilding the
    # active concept state.
    with engine.begin() as connection:

        connection.execute(
            text(
                """
                DELETE FROM
                    profile_claim_concepts

                WHERE
                    claim_id IN (
                        SELECT
                            claim_id

                        FROM
                            profile_claims

                        WHERE
                            profile_id =
                                :profile_id
                    );
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
                    profile_evidence_concepts

                WHERE
                    evidence_id IN (
                        SELECT
                            evidence_id

                        FROM
                            profile_evidence

                        WHERE
                            profile_id =
                                :profile_id
                    );
                """
            ),
            {
                "profile_id":
                    profile_id,
            },
        )


    if not concepts:

        return {
            "profile_id":
                profile_id,

            "profile_name":
                profile[
                    "profile_name"
                ],

            "claims":
                len(claims),

            "evidence":
                len(evidence),

            "active_concepts":
                0,

            "confirmed_claim_links":
                0,

            "candidate_claim_links":
                0,

            "confirmed_evidence_links":
                0,

            "candidate_evidence_links":
                0,
        }


    model = get_model()


    concept_names = [
        concept[
            "canonical_name"
        ]

        for concept
        in concepts
    ]


    concept_embeddings = (
        model.encode(
            concept_names,
            normalize_embeddings=True,
        )
    )


    confirmed_claims = 0
    candidate_claims = 0

    confirmed_evidence = 0
    candidate_evidence = 0


    for claim in claims:

        allowed_types = (
            CLAIM_ALLOWED_TYPES.get(
                claim[
                    "claim_type"
                ],
                SKILL_LIKE_TYPES,
            )
        )


        directly_matched_ids = (
            direct_matches(
                raw_text=
                    claim[
                        "raw_text"
                    ],

                concepts=
                    concepts,

                aliases_by_concept=
                    aliases_by_concept,

                allowed_types=
                    allowed_types,
            )
        )


        curated_candidates = (
            curated_candidate_matches(
                raw_text=
                    claim[
                        "raw_text"
                    ],

                concepts=
                    concepts,

                allowed_types=
                    allowed_types,

                excluded_ids=
                    directly_matched_ids,
            )
        )


        with engine.begin() as connection:

            for concept_id in (
                directly_matched_ids
            ):

                connection.execute(
                    text(
                        """
                        INSERT INTO
                            profile_claim_concepts (
                                claim_id,
                                concept_id,
                                match_method,
                                similarity,
                                review_status,
                                mapper_version
                            )

                        VALUES (
                            :claim_id,
                            :concept_id,
                            'direct_alias',
                            1.0,
                            'confirmed',
                            :mapper_version
                        )

                        ON CONFLICT DO NOTHING;
                        """
                    ),
                    {
                        "claim_id":
                            claim[
                                "claim_id"
                            ],

                        "concept_id":
                            concept_id,

                        "mapper_version":
                            MAPPER_VERSION,
                    },
                )


                confirmed_claims += 1


            for concept_id in (
                curated_candidates
            ):

                connection.execute(
                    text(
                        """
                        INSERT INTO
                            profile_claim_concepts (
                                claim_id,
                                concept_id,
                                match_method,
                                similarity,
                                review_status,
                                mapper_version
                            )

                        VALUES (
                            :claim_id,
                            :concept_id,
                            'curated_candidate',
                            1.0,
                            'candidate',
                            :mapper_version
                        )

                        ON CONFLICT DO NOTHING;
                        """
                    ),
                    {
                        "claim_id":
                            claim[
                                "claim_id"
                            ],

                        "concept_id":
                            concept_id,

                        "mapper_version":
                            MAPPER_VERSION,
                    },
                )


                candidate_claims += 1


        normalized_claim = (
            normalize_concept(
                claim[
                    "raw_text"
                ]
            )
        )


        run_semantic = (
            not directly_matched_ids

            or

            len(
                normalized_claim.split()
            ) >= 4
        )


        if not run_semantic:
            continue


        eligible_indexes = (
            allowed_concept_indexes(
                concepts,
                allowed_types,
            )
        )


        excluded_ids = (
            directly_matched_ids
            |
            curated_candidates
        )


        candidates = (
            semantic_candidates(
                raw_text=
                    claim[
                        "raw_text"
                    ],

                concepts=
                    concepts,

                concept_embeddings=
                    concept_embeddings,

                eligible_indexes=
                    eligible_indexes,

                excluded_ids=
                    excluded_ids,

                threshold=
                    CLAIM_SIMILARITY_THRESHOLD,

                model=
                    model,
            )
        )


        with engine.begin() as connection:

            for (
                concept_id,
                similarity,
            ) in candidates:

                connection.execute(
                    text(
                        """
                        INSERT INTO
                            profile_claim_concepts (
                                claim_id,
                                concept_id,
                                match_method,
                                similarity,
                                review_status,
                                mapper_version
                            )

                        VALUES (
                            :claim_id,
                            :concept_id,
                            'semantic_candidate',
                            :similarity,
                            'candidate',
                            :mapper_version
                        )

                        ON CONFLICT DO NOTHING;
                        """
                    ),
                    {
                        "claim_id":
                            claim[
                                "claim_id"
                            ],

                        "concept_id":
                            concept_id,

                        "similarity":
                            similarity,

                        "mapper_version":
                            MAPPER_VERSION,
                    },
                )


                candidate_claims += 1


    for item in evidence:

        allowed_types = (
            EVIDENCE_ALLOWED_TYPES.get(
                item[
                    "evidence_type"
                ],
                SKILL_LIKE_TYPES,
            )
        )


        directly_matched_ids = (
            direct_matches(
                raw_text=
                    item[
                        "raw_text"
                    ],

                concepts=
                    concepts,

                aliases_by_concept=
                    aliases_by_concept,

                allowed_types=
                    allowed_types,
            )
        )


        curated_candidates = (
            curated_candidate_matches(
                raw_text=
                    item[
                        "raw_text"
                    ],

                concepts=
                    concepts,

                allowed_types=
                    allowed_types,

                excluded_ids=
                    directly_matched_ids,
            )
        )


        with engine.begin() as connection:

            for concept_id in (
                directly_matched_ids
            ):

                connection.execute(
                    text(
                        """
                        INSERT INTO
                            profile_evidence_concepts (
                                evidence_id,
                                concept_id,
                                match_method,
                                similarity,
                                review_status,
                                mapper_version
                            )

                        VALUES (
                            :evidence_id,
                            :concept_id,
                            'direct_alias',
                            1.0,
                            'confirmed',
                            :mapper_version
                        )

                        ON CONFLICT DO NOTHING;
                        """
                    ),
                    {
                        "evidence_id":
                            item[
                                "evidence_id"
                            ],

                        "concept_id":
                            concept_id,

                        "mapper_version":
                            MAPPER_VERSION,
                    },
                )


                confirmed_evidence += 1


            for concept_id in (
                curated_candidates
            ):

                connection.execute(
                    text(
                        """
                        INSERT INTO
                            profile_evidence_concepts (
                                evidence_id,
                                concept_id,
                                match_method,
                                similarity,
                                review_status,
                                mapper_version
                            )

                        VALUES (
                            :evidence_id,
                            :concept_id,
                            'curated_candidate',
                            1.0,
                            'candidate',
                            :mapper_version
                        )

                        ON CONFLICT DO NOTHING;
                        """
                    ),
                    {
                        "evidence_id":
                            item[
                                "evidence_id"
                            ],

                        "concept_id":
                            concept_id,

                        "mapper_version":
                            MAPPER_VERSION,
                    },
                )


                candidate_evidence += 1


        eligible_indexes = (
            allowed_concept_indexes(
                concepts,
                allowed_types,
            )
        )


        excluded_ids = (
            directly_matched_ids
            |
            curated_candidates
        )


        candidates = (
            semantic_candidates(
                raw_text=
                    item[
                        "raw_text"
                    ],

                concepts=
                    concepts,

                concept_embeddings=
                    concept_embeddings,

                eligible_indexes=
                    eligible_indexes,

                excluded_ids=
                    excluded_ids,

                threshold=
                    EVIDENCE_SIMILARITY_THRESHOLD,

                model=
                    model,
            )
        )


        with engine.begin() as connection:

            for (
                concept_id,
                similarity,
            ) in candidates:

                connection.execute(
                    text(
                        """
                        INSERT INTO
                            profile_evidence_concepts (
                                evidence_id,
                                concept_id,
                                match_method,
                                similarity,
                                review_status,
                                mapper_version
                            )

                        VALUES (
                            :evidence_id,
                            :concept_id,
                            'semantic_candidate',
                            :similarity,
                            'candidate',
                            :mapper_version
                        )

                        ON CONFLICT DO NOTHING;
                        """
                    ),
                    {
                        "evidence_id":
                            item[
                                "evidence_id"
                            ],

                        "concept_id":
                            concept_id,

                        "similarity":
                            similarity,

                        "mapper_version":
                            MAPPER_VERSION,
                    },
                )


                candidate_evidence += 1


    return {
        "profile_id":
            profile_id,

        "profile_name":
            profile[
                "profile_name"
            ],

        "claims":
            len(claims),

        "evidence":
            len(evidence),

        "active_concepts":
            len(concepts),

        "confirmed_claim_links":
            confirmed_claims,

        "candidate_claim_links":
            candidate_claims,

        "confirmed_evidence_links":
            confirmed_evidence,

        "candidate_evidence_links":
            candidate_evidence,
    }


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Map CareerCompass profile "
            "claims and evidence onto "
            "the active requirement "
            "concept vocabulary."
        )
    )


    parser.add_argument(
        "--profile-id",
        type=int,
        required=True,
    )


    args = parser.parse_args()


    result = map_profile_concepts(
        profile_id=
            args.profile_id
    )


    print(
        f"Profile: "
        f"{result['profile_name']}"
    )


    print(
        f"Active concepts: "
        f"{result['active_concepts']}"
    )


    print(
        f"Confirmed claim links: "
        f"{result['confirmed_claim_links']}"
    )


    print(
        f"Claim candidates: "
        f"{result['candidate_claim_links']}"
    )


    print(
        f"Confirmed evidence links: "
        f"{result['confirmed_evidence_links']}"
    )


    print(
        f"Evidence candidates: "
        f"{result['candidate_evidence_links']}"
    )


    print(
        "Profile concept mapping complete."
    )