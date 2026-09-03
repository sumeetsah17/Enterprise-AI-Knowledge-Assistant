# ======================================================
# EVIDENCE VALIDATION SERVICE
# ======================================================

# Minimum score required from the BEST reranked chunk.
#
# IMPORTANT:
# CrossEncoder scores are model scores, not probabilities.
# We therefore use this only to determine whether there is
# at least SOME strong evidence.
#
# The reranker already determines the top relevant chunks.
BEST_SCORE_THRESHOLD = 0.0


def validate_evidence(
    scored_chunks: list,
    threshold: float = BEST_SCORE_THRESHOLD
):
    """
    Validate whether the retrieval pipeline found
    sufficient evidence.

    scored_chunks:

        [
            (chunk, rerank_score),
            ...
        ]

    Important design:

    The reranker decides which chunks are the best
    candidates.

    The evidence gate only decides whether the overall
    retrieval is strong enough.

    It does NOT remove lower-scoring chunks from the
    reranker's approved top-K results.
    """

    # --------------------------------------------------
    # No chunks
    # --------------------------------------------------

    if not scored_chunks:

        print()
        print("==============================================")
        print("EVIDENCE GATE")
        print("==============================================")
        print("No reranked chunks received.")
        print("Evidence: INSUFFICIENT")
        print("==============================================")
        print()

        return {
            "has_evidence": False,
            "chunks": []
        }


    # --------------------------------------------------
    # Find the strongest evidence
    # --------------------------------------------------

    best_chunk, best_score = scored_chunks[0]

    best_score = float(best_score)


    # --------------------------------------------------
    # Debug
    # --------------------------------------------------

    print()
    print("==============================================")
    print("EVIDENCE GATE")
    print("==============================================")

    print(
        f"Threshold: {threshold}"
    )

    print(
        f"Best rerank score: "
        f"{best_score:.4f}"
    )

    print(
        f"Best chunk: "
        f"{best_chunk.id}"
    )


    # --------------------------------------------------
    # Evidence decision
    # --------------------------------------------------

    if best_score >= threshold:

        print("Evidence: SUFFICIENT")

        # IMPORTANT:
        #
        # Return ALL reranked top-K chunks.
        #
        # Do not throw away chunks merely because their
        # CrossEncoder score is below zero.
        #
        approved_chunks = [
            chunk
            for chunk, score in scored_chunks
        ]

        print(
            f"Approved chunks: "
            f"{len(approved_chunks)}"
        )

        has_evidence = True

    else:

        print("Evidence: INSUFFICIENT")

        approved_chunks = []

        has_evidence = False


    print("==============================================")
    print()


    return {
        "has_evidence": has_evidence,
        "chunks": approved_chunks
    }