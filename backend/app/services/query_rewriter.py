from app.services.llm_service import rewrite_query


def build_retrieval_query(
    question: str,
    conversation_history: str
) -> str:

    # No history means there is nothing to rewrite.
    if not conversation_history.strip():
        return question

    return rewrite_query(
        question=question,
        conversation_history=conversation_history
    )