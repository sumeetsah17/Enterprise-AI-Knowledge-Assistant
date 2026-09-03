from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)

from sqlalchemy.sql import func

from app.db.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    # ==================================================
    # CONVERSATION ID
    # ==================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ==================================================
    # USER
    # ==================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # ==================================================
    # DOCUMENT
    #
    # Every conversation belongs to one document.
    # This prevents RAG from searching unrelated
    # documents belonging to the same user.
    # ==================================================

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False
    )

    # ==================================================
    # TITLE
    # ==================================================

    title = Column(
        String(255),
        nullable=False,
        default="New Conversation"
    )

    # ==================================================
    # CREATED AT
    # ==================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )