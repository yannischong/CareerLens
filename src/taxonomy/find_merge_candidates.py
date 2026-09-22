from sentence_transformers import (
    SentenceTransformer,
)

from dotenv import load_dotenv
from sqlalchemy import text

from src.collection.database import (
    create_database_engine,
)


MODEL_NAME = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)

SIMILARITY_THRESHOLD = 0.80


load_dotenv()

engine = create_database_engine()


with engine.begin() as connection:

    concepts = (
        connection.execute(
            text(
                """
                SELECT
                    concept_id,
                    concept_type,
                    canonical_name

                FROM requirement_concepts

                ORDER BY concept_id;
                """
            )
        )
        .mappings()
        .all()
    )


if len(concepts) < 2:

    print(
        "Not enough concepts "
        "to compare."
    )

    raise SystemExit


model = SentenceTransformer(
    MODEL_NAME
)


names = [
    concept["canonical_name"]
    for concept in concepts
]


embeddings = model.encode(
    names,
    normalize_embeddings=True,
)


detected = 0


for index_a in range(
    len(concepts)
):

    for index_b in range(
        index_a + 1,
        len(concepts),
    ):

        concept_a = concepts[
            index_a
        ]

        concept_b = concepts[
            index_b
        ]


        if (
            concept_a["concept_type"]
            !=
            concept_b["concept_type"]
        ):
            continue


        similarity = float(
            embeddings[index_a]
            @ embeddings[index_b]
        )


        if (
            similarity
            <
            SIMILARITY_THRESHOLD
        ):
            continue


        concept_id_a = min(
            concept_a["concept_id"],
            concept_b["concept_id"],
        )

        concept_id_b = max(
            concept_a["concept_id"],
            concept_b["concept_id"],
        )


        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    INSERT INTO
                        concept_merge_candidates (
                            concept_id_a,
                            concept_id_b,
                            similarity,
                            match_method
                        )

                    VALUES (
                        :concept_id_a,
                        :concept_id_b,
                        :similarity,
                        :match_method
                    )

                    ON CONFLICT (
                        concept_id_a,
                        concept_id_b
                    )

                    DO UPDATE SET
                        similarity =
                            EXCLUDED.similarity,

                        match_method =
                            EXCLUDED.match_method,

                        detected_at =
                            NOW();
                    """
                ),
                {
                    "concept_id_a":
                        concept_id_a,

                    "concept_id_b":
                        concept_id_b,

                    "similarity":
                        similarity,

                    "match_method":
                        MODEL_NAME,
                },
            )


        detected += 1


print(
    f"Detected "
    f"{detected} "
    f"possible concept merges."
)