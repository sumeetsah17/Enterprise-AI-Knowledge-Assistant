from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    filename = Column(
        String(255),
        nullable=False
    )

    filepath = Column(
        String(500),
        nullable=False
    )

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )