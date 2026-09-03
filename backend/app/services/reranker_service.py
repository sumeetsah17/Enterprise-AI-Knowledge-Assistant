from sentence_transformers import CrossEncoder


# ======================================================
# RERANKER MODEL
# ======================================================

MODEL_NAME = (
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


reranker = CrossEncoder(
    MODEL_NAME
)


# ======================================================
# RERANK CHUNKS
# ======================================================

def rerank_chunks(
    query: str,
    chunks: list,
    top_k: int = 6
):
    """
    Rerank vector-search candidates.

    Returns:

        [
            (chunk, rerank_score),
            ...
        ]

    Important:

    CrossEncoder scores are ranking scores.
    They are NOT probabilities.
    """

    # --------------------------------------------------
    # No candidates
    # --------------------------------------------------

    if not chunks:

        print()
        print("==============================================")
        print("RERANKING DEBUG")
        print("==============================================")
        print("No candidate chunks received.")
        print("==============================================")
        print()

        return []

    # --------------------------------------------------
    # 1. Create query/chunk pairs
    # --------------------------------------------------

    pairs = [
        [
            query,
            chunk.chunk_text
        ]
        for chunk in chunks
    ]

    # --------------------------------------------------
    # 2. Generate scores
    # --------------------------------------------------

    scores = reranker.predict(
        pairs
    )

    # --------------------------------------------------
    # 3. Combine chunks + scores
    # --------------------------------------------------

    scored_chunks = list(
        zip(
            chunks,
            scores
        )
    )

    # --------------------------------------------------
    # 4. Sort highest score first
    # --------------------------------------------------

    scored_chunks.sort(
        key=lambda item: float(item[1]),
        reverse=True
    )

    # --------------------------------------------------
    # 5. Keep top K
    # --------------------------------------------------

    top_chunks = scored_chunks[:top_k]

    # --------------------------------------------------
    # 6. Debug
    # --------------------------------------------------

    print()
    print("==============================================")
    print("RERANKING DEBUG")
    print("==============================================")
    print(f"Query: {query}")
    print()

    for chunk, score in top_chunks:

        print(
            f"Chunk {chunk.id} | "
            f"Document {chunk.document_id} | "
            f"Rerank Score: {float(score):.4f}"
        )

    print("==============================================")
    print()

    return top_chunks