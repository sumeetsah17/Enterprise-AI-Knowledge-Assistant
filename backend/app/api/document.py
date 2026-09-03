from pathlib import Path
import uuid

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.db.database import get_db

from app.models.document import Document
from app.models.chunk import Chunk
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message

from app.auth.dependencies import get_current_user

from app.services.pdf_service import extract_text_from_pdf
from app.services.chunk_service import split_text
from app.services.embedding_service import generate_embedding

from app.services.search_service import (
    search_similar_chunks,
    search_document_overview_chunks,
    find_document_by_filename
)

from app.services.llm_service import generate_answer

from app.services.query_router import classify_query
from app.services.query_rewriter import build_retrieval_query

from app.services.reranker_service import rerank_chunks
from app.services.evidence_service import validate_evidence

from app.services.summary_service import summarize_document

from app.schemas.search import SearchRequest
from app.schemas.chat import ChatRequest


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)


# ======================================================
# UPLOAD DOCUMENT
# ======================================================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # --------------------------------------------------
    # 1. Validate filename
    # --------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    # --------------------------------------------------
    # 2. Only allow PDF files
    # --------------------------------------------------

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # --------------------------------------------------
    # 3. Check duplicate filename
    # --------------------------------------------------

    existing_document = (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id,
            Document.filename == file.filename
        )
        .first()
    )

    if existing_document:

        raise HTTPException(
            status_code=409,
            detail=(
                "You have already uploaded a document "
                "with this filename"
            )
        )

    # --------------------------------------------------
    # 4. User-specific upload folder
    # --------------------------------------------------

    user_upload_folder = (
        UPLOAD_FOLDER /
        str(current_user.id)
    )

    user_upload_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------
    # 5. Unique physical filename
    # --------------------------------------------------

    unique_filename = (
        f"{uuid.uuid4()}_{file.filename}"
    )

    file_path = (
        user_upload_folder /
        unique_filename
    )

    # --------------------------------------------------
    # 6. Save PDF
    # --------------------------------------------------

    try:

        with open(
            file_path,
            "wb"
        ) as buffer:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                buffer.write(chunk)

    except Exception:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Failed to save uploaded file"
        )

    # --------------------------------------------------
    # 7. Extract text
    # --------------------------------------------------

    try:

        text = extract_text_from_pdf(
            str(file_path)
        )

    except Exception:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=400,
            detail="Could not read the PDF file"
        )

    # --------------------------------------------------
    # 8. Split into chunks
    # --------------------------------------------------

    chunks = split_text(text)

    if not chunks:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=400,
            detail=(
                "No readable text found in the PDF"
            )
        )

    # --------------------------------------------------
    # 9. Save document
    # --------------------------------------------------

    document = Document(
        user_id=current_user.id,
        filename=file.filename,
        filepath=str(file_path)
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # --------------------------------------------------
    # 10. Generate embeddings
    # --------------------------------------------------

    try:

        for chunk_text in chunks:

            embedding = generate_embedding(
                chunk_text
            )

            chunk_record = Chunk(
                document_id=document.id,
                chunk_text=chunk_text,
                embedding=embedding
            )

            db.add(chunk_record)

        db.commit()

    except Exception:

        db.rollback()

        if file_path.exists():
            file_path.unlink()

        db.delete(document)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate embeddings"
            )
        )

    # --------------------------------------------------
    # 11. Return result
    # --------------------------------------------------

    return {
        "message": "File uploaded successfully",
        "id": document.id,
        "filename": document.filename,
        "chunks_created": len(chunks),
        "user_id": current_user.id
    }


# ======================================================
# GET MY DOCUMENTS
# ======================================================

@router.get("/")
def get_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    documents = (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id
        )
        .order_by(
            Document.id.desc()
        )
        .all()
    )

    return [
        {
            "id": document.id,
            "filename": document.filename,
            "filepath": document.filepath,
            "uploaded_at": document.uploaded_at
        }
        for document in documents
    ]


# ======================================================
# DOCUMENT SUMMARY
# ======================================================

@router.get("/{document_id}/summary")
def get_document_summary(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # --------------------------------------------------
    # 1. Find document
    # --------------------------------------------------

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
        .first()
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # --------------------------------------------------
    # 2. Generate summary
    # --------------------------------------------------

    summary = summarize_document(
        document_id=document.id,
        filename=document.filename,
        db=db
    )

    if summary is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Document has no content to summarize"
            )
        )

    # --------------------------------------------------
    # 3. Return summary
    # --------------------------------------------------

    return {
        "document_id": document.id,
        "filename": document.filename,
        "summary": summary
    }


# ======================================================
# DELETE DOCUMENT
# ======================================================

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # --------------------------------------------------
    # 1. Find document
    # --------------------------------------------------

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
        .first()
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # --------------------------------------------------
    # 2. Delete chunks
    # --------------------------------------------------

    db.query(Chunk).filter(
        Chunk.document_id == document.id
    ).delete(
        synchronize_session=False
    )

    # --------------------------------------------------
    # 3. Delete physical PDF
    # --------------------------------------------------

    file_path = Path(
        document.filepath
    )

    if file_path.exists():
        file_path.unlink()

    # --------------------------------------------------
    # 4. Delete document
    # --------------------------------------------------

    db.delete(document)
    db.commit()

    return {
        "message": (
            "Document deleted successfully"
        ),
        "document_id": document_id
    }


# ======================================================
# SEMANTIC SEARCH
# ======================================================

@router.post("/search")
def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    results = search_similar_chunks(
        query=request.query,
        db=db,
        top_k=5,
        user_id=current_user.id
    )

    return {
        "query": request.query,
        "results": [
            {
                "chunk_id": result.id,
                "document_id": result.document_id,
                "text": result.chunk_text
            }
            for result in results
        ]
    }


# ======================================================
# DOCUMENT CHAT
# ======================================================

@router.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # ==================================================
    # 1. FIND CONVERSATION
    # ==================================================

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id ==
            request.conversation_id,

            Conversation.user_id ==
            current_user.id
        )
        .first()
    )

    if conversation is None:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    # ==================================================
    # 2. GET PREVIOUS MESSAGES
    # ==================================================

    previous_messages = (
        db.query(Message)
        .filter(
            Message.conversation_id ==
            conversation.id
        )
        .order_by(
            Message.id.asc()
        )
        .all()
    )

    # ==================================================
    # 3. BUILD CONVERSATION HISTORY
    # ==================================================

    conversation_history = "\n".join(
        f"{message.role}: {message.content}"
        for message in previous_messages
    )

    # ==================================================
    # 4. SAVE USER QUESTION
    # ==================================================

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.question
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # ==================================================
    # 5. CLASSIFY QUERY
    # ==================================================

    query_type = classify_query(
        request.question
    )

    print()
    print("==============================================")
    print("QUERY TYPE:")
    print(query_type)
    print("==============================================")
    print()

    # ==================================================
    # 6. INITIALIZE
    # ==================================================

    results = []

    retrieval_query = request.question

    # ==================================================
    # 7. BUILD REWRITTEN QUERY
    # ==================================================

    if query_type in {
        "document",
        "document_overview"
    }:

        retrieval_query = build_retrieval_query(
            question=request.question,
            conversation_history=conversation_history
        )

        print()
        print("==============================================")
        print("REWRITTEN RETRIEVAL QUERY:")
        print(retrieval_query)
        print("==============================================")
        print()

    # ==================================================
    # 8. NORMAL DOCUMENT RAG
    # ==================================================

    if query_type == "document":

        # --------------------------------------------------
        # Vector search
        # --------------------------------------------------

        candidate_chunks = search_similar_chunks(
            query=retrieval_query,
            db=db,
            top_k=20,
            user_id=current_user.id,
            document_id=conversation.document_id,
            similarity_threshold=0.10
        )

        print()
        print("==============================================")
        print("VECTOR SEARCH RESULTS:")
        print("==============================================")

        for chunk in candidate_chunks:

            print(
                f"Chunk {chunk.id} | "
                f"Document {chunk.document_id}"
            )

        print("==============================================")
        print()

        # --------------------------------------------------
        # Reranking
        # --------------------------------------------------

        reranked_chunks = rerank_chunks(
            query=retrieval_query,
            chunks=candidate_chunks,
            top_k=6
        )

        # --------------------------------------------------
        # Evidence gate
        # --------------------------------------------------

        evidence = validate_evidence(
            scored_chunks=reranked_chunks
        )

        if evidence["has_evidence"]:

            results = evidence["chunks"]

        else:

            results = []

        # --------------------------------------------------
        # Debug
        # --------------------------------------------------

        print()
        print("==============================================")
        print("RERANKED / APPROVED RESULTS:")
        print("==============================================")

        for chunk in results:

            print(
                f"Chunk {chunk.id} | "
                f"Document {chunk.document_id}"
            )

        print("==============================================")
        print()

    # ==================================================
    # 9. DOCUMENT OVERVIEW RAG
    # ==================================================

    elif query_type == "document_overview":

        # --------------------------------------------------
        # Start with the document attached to this conversation.
        # --------------------------------------------------

        target_document = None

        if conversation.document_id is not None:

            target_document = (
                db.query(Document)
                .filter(
                    Document.id == conversation.document_id,
                    Document.user_id == current_user.id
                )
                .first()
            )

        # --------------------------------------------------
        # First check exact filenames from user's documents.
        # An explicitly named filename may override the
        # conversation's default document.
        # --------------------------------------------------

        user_documents = (
            db.query(Document)
            .filter(
                Document.user_id ==
                current_user.id
            )
            .order_by(
                Document.id.desc()
            )
            .all()
        )

        normalized_question = (
            request.question.lower()
        )

        for document in user_documents:

            filename = (
                document.filename.lower()
            )

            if filename in normalized_question:

                target_document = document
                break

        # --------------------------------------------------
        # If exact filename wasn't found, try common
        # filename without extension.
        # --------------------------------------------------

        if target_document is None:

            for document in user_documents:

                filename_without_extension = (
                    Path(
                        document.filename
                    ).stem.lower()
                )

                if (
                    filename_without_extension
                    in normalized_question
                ):

                    target_document = document
                    break

        # --------------------------------------------------
        # Debug document selection
        # --------------------------------------------------

        print()
        print("==============================================")
        print("DOCUMENT OVERVIEW TARGET")
        print("==============================================")

        if target_document:

            print(
                f"Document ID: "
                f"{target_document.id}"
            )

            print(
                f"Filename: "
                f"{target_document.filename}"
            )

        else:

            print(
                "No explicit document identified."
            )

        print("==============================================")
        print()

        # --------------------------------------------------
        # Broad document retrieval
        # --------------------------------------------------

        results = search_document_overview_chunks(
            db=db,
            user_id=current_user.id,
            document_id=(
                target_document.id
                if target_document
                else None
            ),
            max_chunks=12,
            semantic_query=retrieval_query
        )

        # --------------------------------------------------
        # Broad retrieval debug
        # --------------------------------------------------

        print()
        print("==============================================")
        print("DOCUMENT OVERVIEW RESULTS")
        print("==============================================")

        for chunk in results:

            print(
                f"Chunk {chunk.id} | "
                f"Document {chunk.document_id}"
            )

        print("==============================================")
        print()

    # ==================================================
    # 10. BUILD FINAL CONTEXT
    # ==================================================

    context = "\n\n".join(
        result.chunk_text
        for result in results
    )

    print()
    print("==============================================")
    print("FINAL LLM CONTEXT")
    print("==============================================")

    print(
        f"Context chunks: "
        f"{len(results)}"
    )

    for result in results:

        print()
        print(
            f"--- Chunk {result.id} "
            f"| Document {result.document_id} ---"
        )

        print(
            result.chunk_text[:1000]
        )

    print()
    print("==============================================")
    print()

    # ==================================================
    # 11. GENERATE ANSWER
    # ==================================================

    if (
        query_type in {
            "document",
            "document_overview"
        }
        and not results
    ):

        answer = (
            "I don't have enough information "
            "in the provided documents."
        )

    else:

        answer = generate_answer(
            question=request.question,
            context=context,
            conversation_history=conversation_history,
            mode=(
                "document"
                if query_type ==
                "document_overview"
                else query_type
            )
        )

    # ==================================================
    # 12. SAVE AI ANSWER
    # ==================================================

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    # ==================================================
    # 13. BUILD SOURCES
    # ==================================================

    sources = []

    seen_sources = set()

    for result in results:

        document = (
            db.query(Document)
            .filter(
                Document.id ==
                result.document_id,

                Document.user_id ==
                current_user.id
            )
            .first()
        )

        if document is None:
            continue

        source_key = (
            result.id,
            result.document_id
        )

        if source_key in seen_sources:
            continue

        seen_sources.add(
            source_key
        )

        sources.append({
            "chunk_id": result.id,
            "document_id": result.document_id,
            "filename": document.filename
        })

    # ==================================================
    # 14. RETURN RESPONSE
    # ==================================================

    return {
        "conversation_id": conversation.id,
        "question": request.question,
        "answer": answer,
        "sources": sources
    }