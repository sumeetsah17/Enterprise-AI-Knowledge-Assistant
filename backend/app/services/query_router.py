# ======================================================
# QUERY ROUTER
# ======================================================

def classify_query(question: str) -> str:
    """
    Classify the user's message before running RAG.

    Returns:

        "casual"
            Normal conversation that does not require
            document retrieval.

        "document"
            Specific document question that should use
            normal vector search + reranking.

        "document_overview"
            Broad/document-level question that requires
            wider document coverage rather than only the
            most semantically similar chunks.
    """

    normalized = question.strip().lower()

    # --------------------------------------------------
    # Empty input
    # --------------------------------------------------

    if not normalized:
        return "casual"

    # --------------------------------------------------
    # Casual greetings / short conversational messages
    # --------------------------------------------------

    casual_messages = {
        "hi",
        "hii",
        "hiii",
        "hello",
        "hey",
        "heyy",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
        "thanks",
        "thank you",
        "thankyou",
        "thx",
        "ok",
        "okay",
        "cool",
        "great",
        "nice",
        "bye",
        "goodbye"
    }

    if normalized in casual_messages:
        return "casual"

    # --------------------------------------------------
    # Common casual phrases
    # --------------------------------------------------

    casual_phrases = [
        "how are you",
        "how are you doing",
        "what's up",
        "whats up",
        "who are you",
        "what can you do",
        "nice to meet you"
    ]

    if any(
        phrase in normalized
        for phrase in casual_phrases
    ):
        return "casual"

    # ==================================================
    # DOCUMENT OVERVIEW / BROAD QUESTIONS
    # ==================================================

    # These questions normally require information from
    # multiple parts of a document rather than one
    # specific passage.

    overview_phrases = [
        "summarize this document",
        "summarize the document",
        "summarise this document",
        "summarise the document",

        "give me a summary",
        "give me an overview",
        "give me overview",

        "what is this document about",
        "what does this document discuss",
        "what does the document discuss",

        "what are the main principles",
        "what are the main concepts",
        "what are the key concepts",
        "what are the main topics",
        "what are the key topics",

        "what are the major topics",
        "what are the main ideas",
        "what are the key ideas",

        "what are the important points",
        "what are the main points",
        "what are the key points",

        "explain the document",
        "explain this document",

        "overview of the document",
        "overview of this document",

        "main principles discussed",
        "key principles discussed",

        "main concepts discussed",
        "key concepts discussed",

        "main topics discussed",
        "key topics discussed",

        "major themes",
        "main themes",
        "key themes"
    ]

    if any(
        phrase in normalized
        for phrase in overview_phrases
    ):
        return "document_overview"

    # --------------------------------------------------
    # Broad question patterns
    # --------------------------------------------------

    broad_starts = [
        "summarize ",
        "summarise ",
        "overview ",
        "give me an overview",
        "give an overview",
        "what does this pdf cover",
        "what does this paper cover",
        "what does this report cover",
        "what does this file cover",
        "what is covered in this document"
    ]

    if any(
        normalized.startswith(prefix)
        for prefix in broad_starts
    ):
        return "document_overview"

    # ==================================================
    # DEFAULT
    # ==================================================

    # Everything else goes through normal document RAG.

    return "document"