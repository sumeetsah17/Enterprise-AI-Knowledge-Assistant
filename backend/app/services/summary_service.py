from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.services.llm_service import (
    generate_document_summary
)


# ======================================================
# CONFIGURATION
# ======================================================

# Process more chunks per Gemini request.
#
# Previous:
#     5 chunks
#
# New:
#     15 chunks
#
# This significantly reduces Gemini API calls.

SUMMARY_BATCH_SIZE = 15


# Number of partial summaries combined during reduction.
REDUCE_BATCH_SIZE = 3


# ======================================================
# HELPER
# ======================================================

def _create_batches(
    items,
    batch_size: int
):
    """
    Split items into smaller batches.
    """

    return [
        items[start:start + batch_size]
        for start in range(
            0,
            len(items),
            batch_size
        )
    ]


# ======================================================
# REDUCE SUMMARIES
# ======================================================

def _reduce_summaries(
    summaries,
    filename: str
):
    """
    Recursively combine partial summaries.

    Example:

        6 summaries
             ↓
        groups of 3
             ↓
        2 summaries
             ↓
        1 final summary
    """

    current_summaries = summaries

    level = 1

    while len(current_summaries) > 1:

        print()
        print(
            "=============================================="
        )
        print(
            f"SUMMARY REDUCTION LEVEL {level}"
        )
        print(
            "=============================================="
        )

        print(
            f"Input summaries: "
            f"{len(current_summaries)}"
        )

        reduce_batches = _create_batches(
            current_summaries,
            REDUCE_BATCH_SIZE
        )

        print(
            f"Reduction batches: "
            f"{len(reduce_batches)}"
        )

        next_summaries = []

        for index, batch in enumerate(
            reduce_batches,
            start=1
        ):

            print(
                f"Reducing batch "
                f"{index}/{len(reduce_batches)}..."
            )

            combined_text = "\n\n".join(
                f"SECTION {section_index}:\n{summary}"
                for section_index, summary
                in enumerate(
                    batch,
                    start=1
                )
            )

            reduced_summary = (
                generate_document_summary(
                    text=combined_text,
                    filename=filename
                )
            )

            if (
                reduced_summary
                and reduced_summary.strip()
            ):

                next_summaries.append(
                    reduced_summary.strip()
                )

        if not next_summaries:

            raise RuntimeError(
                "Summary reduction produced "
                "no valid summaries."
            )

        current_summaries = (
            next_summaries
        )

        print(
            f"Reduction level {level} complete."
        )

        print(
            f"Remaining summaries: "
            f"{len(current_summaries)}"
        )

        level += 1

    return current_summaries[0]


# ======================================================
# SUMMARIZE DOCUMENT
# ======================================================

def summarize_document(
    document_id: int,
    filename: str,
    db: Session
):
    """
    Generate a summary for an entire document.

    Pipeline:

        Document
            ↓
        Chunks
            ↓
        Larger batches
            ↓
        Partial summaries
            ↓
        Recursive reduction
            ↓
        Final summary

    Example for 30 chunks:

        30 chunks
            ↓
        15 + 15
            ↓
        2 partial summaries
            ↓
        1 final summary

    Total Gemini requests:

        3
    """

    # ==================================================
    # 1. LOAD DOCUMENT CHUNKS
    # ==================================================

    chunks = (
        db.query(Chunk)
        .filter(
            Chunk.document_id == document_id
        )
        .order_by(
            Chunk.id.asc()
        )
        .all()
    )

    if not chunks:

        print(
            f"No chunks found for document "
            f"{document_id}."
        )

        return None

    # ==================================================
    # DEBUG
    # ==================================================

    print()
    print(
        "=============================================="
    )
    print(
        "DOCUMENT SUMMARIZATION"
    )
    print(
        "=============================================="
    )

    print(
        f"Document: {filename}"
    )

    print(
        f"Document ID: {document_id}"
    )

    print(
        f"Total chunks: {len(chunks)}"
    )

    print(
        f"Batch size: {SUMMARY_BATCH_SIZE}"
    )

    print(
        "=============================================="
    )
    print()

    # ==================================================
    # 2. CREATE CHUNK BATCHES
    # ==================================================

    batches = _create_batches(
        chunks,
        SUMMARY_BATCH_SIZE
    )

    print(
        f"Summary batches: {len(batches)}"
    )

    # ==================================================
    # 3. SUMMARIZE EACH BATCH
    # ==================================================

    partial_summaries = []

    for index, batch in enumerate(
        batches,
        start=1
    ):

        print()
        print(
            "----------------------------------------------"
        )

        print(
            f"Summarizing batch "
            f"{index}/{len(batches)}"
        )

        print(
            f"Chunks in batch: "
            f"{len(batch)}"
        )

        print(
            "----------------------------------------------"
        )

        batch_text = "\n\n".join(
            chunk.chunk_text
            for chunk in batch
            if chunk.chunk_text
        )

        if not batch_text.strip():

            print(
                "Skipping empty batch."
            )

            continue

        summary = (
            generate_document_summary(
                text=batch_text,
                filename=filename
            )
        )

        if (
            summary
            and summary.strip()
        ):

            partial_summaries.append(
                summary.strip()
            )

    # ==================================================
    # 4. SAFETY CHECK
    # ==================================================

    if not partial_summaries:

        raise RuntimeError(
            "No valid partial summaries "
            "were generated."
        )

    # ==================================================
    # 5. SINGLE BATCH
    # ==================================================

    if len(partial_summaries) == 1:

        print()
        print(
            "Single summary batch."
        )

        print(
            "Using batch summary as final summary."
        )

        print()
        print(
            "=============================================="
        )
        print(
            "DOCUMENT SUMMARY COMPLETE"
        )
        print(
            "=============================================="
        )
        print()

        return partial_summaries[0]

    # ==================================================
    # 6. MULTIPLE BATCHES
    # ==================================================

    print()
    print(
        "Multiple partial summaries detected."
    )

    print(
        "Starting recursive summary reduction..."
    )

    final_summary = _reduce_summaries(
        summaries=partial_summaries,
        filename=filename
    )

    # ==================================================
    # 7. COMPLETE
    # ==================================================

    print()
    print(
        "=============================================="
    )
    print(
        "DOCUMENT SUMMARY COMPLETE"
    )
    print(
        "=============================================="
    )
    print()

    return final_summary