from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document
from app.models.user import User
from app.auth.dependencies import get_current_user


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)


# ======================================================
# CREATE CONVERSATION
# ======================================================

@router.post("/")
def create_conversation(
    document_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # --------------------------------------------------
    # If a document was supplied, verify that it belongs
    # to the currently logged-in user.
    # --------------------------------------------------

    document = None

    if document_id is not None:

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
    # Create conversation
    # --------------------------------------------------

    conversation = Conversation(
        user_id=current_user.id,
        document_id=document_id,
        title="New Conversation"
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    # --------------------------------------------------
    # Return conversation
    # --------------------------------------------------

    return {
        "id": conversation.id,
        "title": conversation.title,
        "user_id": conversation.user_id,
        "document_id": conversation.document_id,
        "created_at": conversation.created_at
    }


# ======================================================
# GET MY CONVERSATIONS
# ======================================================

@router.get("/")
def get_my_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    conversations = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == current_user.id
        )
        .order_by(
            Conversation.id.desc()
        )
        .all()
    )

    return [
        {
            "id": conversation.id,
            "title": conversation.title,
            "document_id": conversation.document_id,
            "created_at": conversation.created_at
        }
        for conversation in conversations
    ]


# ======================================================
# GET SINGLE CONVERSATION
# ======================================================

@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    messages = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation.id
        )
        .order_by(
            Message.id.asc()
        )
        .all()
    )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "document_id": conversation.document_id,
        "created_at": conversation.created_at,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at
            }
            for message in messages
        ]
    }


# ======================================================
# DELETE CONVERSATION
# ======================================================

@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    # --------------------------------------------------
    # Delete messages belonging to conversation
    # --------------------------------------------------

    db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).delete(
        synchronize_session=False
    )

    # --------------------------------------------------
    # Delete conversation
    # --------------------------------------------------

    db.delete(conversation)
    db.commit()

    return {
        "message": "Conversation deleted successfully",
        "conversation_id": conversation_id
    }