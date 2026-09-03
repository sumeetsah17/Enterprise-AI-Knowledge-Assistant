from app.db.database import SessionLocal
from app.services.search_service import search_similar_chunks


def test_search():
    db = SessionLocal()

    try:
        results = search_similar_chunks(
            query="What does the CoffeeMaker class do?",
            db=db,
            top_k=5,
            user_id=1
        )

        print("\n" + "=" * 60)
        print("SEARCH RESULTS")
        print("=" * 60)

        for result in results:
            print(f"\nChunk ID: {result.id}")
            print(f"Document ID: {result.document_id}")
            print(f"Text:\n{result.chunk_text}")

    finally:
        db.close()


if __name__ == "__main__":
    test_search()