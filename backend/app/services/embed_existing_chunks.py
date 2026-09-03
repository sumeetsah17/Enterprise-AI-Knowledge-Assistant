from app.db.database import SessionLocal

from app.models.user import User
from app.models.document import Document
from app.models.chunk import Chunk

from app.services.embedding_service import generate_embedding


def embed_existing_chunks():
    db = SessionLocal()

    try:
        chunks = (
            db.query(Chunk)
            .filter(Chunk.embedding.is_(None))
            .all()
        )

        print(f"Found {len(chunks)} chunks without embeddings.")

        for chunk in chunks:
            chunk.embedding = generate_embedding(chunk.chunk_text)

            print(f"Embedded chunk {chunk.id}")

        db.commit()

        print("All embeddings saved successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    embed_existing_chunks()