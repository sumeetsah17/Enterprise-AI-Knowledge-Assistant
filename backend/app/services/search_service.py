from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document

from app.services.embedding_service import generate_embedding


# ======================================================
# NORMAL SEMANTIC SEARCH
# ======================================================

def search_similar_chunks(
    query: str,
    db: Session,
    top_k: int = 20,
    user_id: int | None = None,
    similarity_threshold: float = 0.10,
    document_id: int | None = None
):
    """
    Stage 1 of normal RAG retrieval.

    Finds semantically similar chunks using pgvector.

    The reranker is responsible for final relevance
    ranking.

    document_id is optional.

    If document_id is supplied, search is restricted
    to that document.
    """

    # --------------------------------------------------
    # 1. Generate query embedding
    # --------------------------------------------------

    query_embedding = generate_embedding(query)

    # --------------------------------------------------
    # 2. Build query
    # --------------------------------------------------

    query_obj = (
        db.query(Chunk)
        .join(
            Document,
            Chunk.document_id == Document.id
        )
        .filter(
            Chunk.embedding.is_not(None)
        )
    )

    # --------------------------------------------------
    # 3. Restrict to current user
    # --------------------------------------------------

    if user_id is not None:

        query_obj = query_obj.filter(
            Document.user_id == user_id
        )

    # --------------------------------------------------
    # 4. Restrict to specific document if requested
    # --------------------------------------------------

    if document_id is not None:

        query_obj = query_obj.filter(
            Document.id == document_id
        )

    # --------------------------------------------------
    # 5. Cosine similarity
    # --------------------------------------------------

    distance = Chunk.embedding.cosine_distance(
        query_embedding
    )

    similarity = 1 - distance

    # --------------------------------------------------
    # 6. Candidate retrieval
    # --------------------------------------------------

    results = (
        query_obj
        .add_columns(
            similarity.label("similarity")
        )
        .filter(
            similarity >= similarity_threshold
        )
        .order_by(
            distance.asc()
        )
        .limit(top_k)
        .all()
    )

    # --------------------------------------------------
    # 7. Debug
    # --------------------------------------------------

    print()
    print("==============================================")
    print("RAG RETRIEVAL DEBUG")
    print("==============================================")
    print(f"Query: {query}")
    print(
        f"Similarity threshold: "
        f"{similarity_threshold}"
    )
    print(
        f"Candidate limit: "
        f"{top_k}"
    )

    if document_id is not None:

        print(
            f"Document filter: "
            f"{document_id}"
        )

    print()

    for result in results:

        chunk = result[0]
        score = result[1]

        print(
            f"Chunk {chunk.id} | "
            f"Document {chunk.document_id} | "
            f"Similarity: {float(score):.4f}"
        )

    print("==============================================")
    print()

    return [
        result[0]
        for result in results
    ]


# ======================================================
# FIND DOCUMENT BY FILENAME
# ======================================================

def find_document_by_filename(
    filename: str,
    db: Session,
    user_id: int
):
    """
    Find a user's document by filename.

    Matching is case-insensitive.

    Returns:

        Document | None
    """

    if not filename:
        return None

    filename = filename.strip()

    # --------------------------------------------------
    # Exact case-insensitive match
    # --------------------------------------------------

    document = (
        db.query(Document)
        .filter(
            Document.user_id == user_id,
            Document.filename.ilike(filename)
        )
        .first()
    )

    if document is not None:
        return document

    # --------------------------------------------------
    # Partial match
    #
    # Useful if the user says:
    #
    # "genai-principles"
    #
    # instead of:
    #
    # "genai-principles.pdf"
    # --------------------------------------------------

    document = (
        db.query(Document)
        .filter(
            Document.user_id == user_id,
            Document.filename.ilike(
                f"%{filename}%"
            )
        )
        .first()
    )

    return document


# ======================================================
# BROAD DOCUMENT RETRIEVAL
# ======================================================

def search_document_overview_chunks(
    db: Session,
    user_id: int,
    document_id: int | None = None,
    max_chunks: int = 12,
    semantic_query: str | None = None
):
    """
    Retrieve a broad representation of a document.

    This is intentionally different from normal RAG.

    Normal RAG asks:

        "Which chunks are most relevant to this
         particular question?"

    Overview retrieval asks:

        "Give me representative coverage across the
         document."

    Strategy:

        1. Get chunks ordered by document position.
        2. Select evenly distributed chunks.
        3. If a semantic query exists, retrieve some
           highly relevant chunks too.
        4. Merge and deduplicate.
        5. Return a bounded context.

    This prevents a document-level question from being
    answered using only the introduction or one section.
    """

    # --------------------------------------------------
    # 1. Find documents
    # --------------------------------------------------

    document_query = (
        db.query(Document)
        .filter(
            Document.user_id == user_id
        )
    )

    if document_id is not None:

        document_query = document_query.filter(
            Document.id == document_id
        )

    documents = (
        document_query
        .order_by(Document.id.desc())
        .all()
    )

    if not documents:

        return []

    # --------------------------------------------------
    # 2. Determine target documents
    #
    # If a document_id was explicitly supplied, use only
    # that document.
    #
    # Otherwise use the user's documents.
    # --------------------------------------------------

    target_document_ids = [
        document.id
        for document in documents
    ]

    # --------------------------------------------------
    # 3. Load chunks in document order
    # --------------------------------------------------

    chunk_query = (
        db.query(Chunk)
        .filter(
            Chunk.document_id.in_(
                target_document_ids
            )
        )
        .order_by(
            Chunk.document_id.asc(),
            Chunk.id.asc()
        )
    )

    all_chunks = chunk_query.all()

    if not all_chunks:

        return []

    # --------------------------------------------------
    # 4. Group chunks by document
    # --------------------------------------------------

    chunks_by_document = {}

    for chunk in all_chunks:

        chunks_by_document.setdefault(
            chunk.document_id,
            []
        ).append(chunk)

    # --------------------------------------------------
    # 5. If there is one specific document, distribute
    #    the chunk budget across that document.
    #
    #    If multiple documents exist, distribute a smaller
    #    number of chunks across documents.
    # --------------------------------------------------

    selected_chunks = []

    if document_id is not None:

        document_chunks = chunks_by_document.get(
            document_id,
            []
        )

        selected_chunks.extend(
            _select_evenly_spaced_chunks(
                document_chunks,
                max_chunks
            )
        )

    else:

        document_count = len(
            chunks_by_document
        )

        if document_count == 0:

            return []

        per_document = max(
            1,
            max_chunks // document_count
        )

        for current_document_id, document_chunks in (
            chunks_by_document.items()
        ):

            selected_chunks.extend(
                _select_evenly_spaced_chunks(
                    document_chunks,
                    per_document
                )
            )

            if len(selected_chunks) >= max_chunks:
                break

    # --------------------------------------------------
    # 6. Semantic retrieval for broad question
    #
    # We use semantic retrieval as a supplement.
    #
    # It does NOT replace representative coverage.
    # --------------------------------------------------

    semantic_chunks = []

    if semantic_query:

        semantic_chunks = search_similar_chunks(
            query=semantic_query,
            db=db,
            top_k=min(8, max_chunks),
            user_id=user_id,
            similarity_threshold=0.05,
            document_id=document_id
        )

    # --------------------------------------------------
    # 7. Merge semantic + representative chunks
    # --------------------------------------------------

    merged = []

    seen_ids = set()

    # Semantic chunks first because they are directly
    # related to the user's question.

    for chunk in semantic_chunks:

        if chunk.id in seen_ids:
            continue

        seen_ids.add(chunk.id)
        merged.append(chunk)

    # Then add representative chunks to guarantee
    # coverage across the document.

    for chunk in selected_chunks:

        if chunk.id in seen_ids:
            continue

        seen_ids.add(chunk.id)
        merged.append(chunk)

    # --------------------------------------------------
    # 8. Limit final context
    # --------------------------------------------------

    merged = merged[:max_chunks]

    # --------------------------------------------------
    # 9. Debug
    # --------------------------------------------------

    print()
    print("==============================================")
    print("DOCUMENT OVERVIEW RETRIEVAL")
    print("==============================================")

    print(
        f"Target document: "
        f"{document_id if document_id else 'ALL'}"
    )

    print(
        f"Semantic candidates: "
        f"{len(semantic_chunks)}"
    )

    print(
        f"Representative candidates: "
        f"{len(selected_chunks)}"
    )

    print(
        f"Final overview chunks: "
        f"{len(merged)}"
    )

    print()

    for index, chunk in enumerate(
        merged,
        start=1
    ):

        print(
            f"{index}. Chunk {chunk.id} | "
            f"Document {chunk.document_id}"
        )

    print("==============================================")
    print()

    return merged


# ======================================================
# EVENLY SPACED CHUNK SELECTION
# ======================================================

def _select_evenly_spaced_chunks(
    chunks: list,
    max_chunks: int
):
    """
    Select chunks distributed across the document.

    Example:

        45 chunks
        max_chunks = 10

    Instead of taking:

        1,2,3,4,5...

    we select approximately:

        1,6,11,16,21,26,31,36,41,45

    This provides much better document coverage.
    """

    if not chunks:

        return []

    if len(chunks) <= max_chunks:

        return list(chunks)

    if max_chunks <= 1:

        return [chunks[0]]

    selected = []

    last_index = len(chunks) - 1

    for i in range(max_chunks):

        position = round(
            i * last_index / (max_chunks - 1)
        )

        chunk = chunks[position]

        if chunk.id not in {
            selected_chunk.id
            for selected_chunk in selected
        }:

            selected.append(chunk)

    return selected