import os
import time

from dotenv import load_dotenv
from groq import Groq
from google import genai
from google.genai import types


# ======================================================
# ENVIRONMENT
# ======================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set in .env"
    )


if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set in .env"
    )


# ======================================================
# CLIENTS
# ======================================================

groq_client = Groq(
    api_key=GROQ_API_KEY
)


gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ======================================================
# MODELS
# ======================================================

GROQ_MODEL_NAME = "openai/gpt-oss-120b"

GEMINI_MODEL_NAME = "gemini-3.5-flash-lite"


# ======================================================
# QUERY REWRITER
# ======================================================

def rewrite_query(
    question: str,
    conversation_history: str
) -> str:

    prompt = f"""
You are a query rewriting component for an enterprise
knowledge retrieval system.

Rewrite the CURRENT question into a standalone search
query when it depends on previous conversation context.

Previous conversation:
{conversation_history}

Current question:
{question}

Rules:

1. If the question is already standalone, return it
   unchanged.

2. Resolve references such as:
   - it
   - this
   - that
   - they
   - its
   - the second method
   - the previous class
   - this function
   - that document

3. Preserve the user's actual intent.

4. Do NOT answer the question.

5. Return ONLY the rewritten search query.

Examples:

Conversation:
User: What is the CoffeeMaker class?

Current:
What does the second method do?

Output:
What does the second method of the CoffeeMaker class do?

---

Conversation:
User: Explain the Employee class.

Current:
What properties does it have?

Output:
What properties does the Employee class have?

---

Conversation:
User: What is the capital of France?

Current:
What is the population of Germany?

Output:
What is the population of Germany?
"""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You rewrite search queries. "
                    "Do not answer questions."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return (
        response.choices[0]
        .message
        .content
        .strip()
    )


# ======================================================
# ANSWER GENERATION
# ======================================================

def generate_answer(
    question: str,
    context: str,
    conversation_history: str = "",
    mode: str = "document"
) -> str:

    # ==================================================
    # DEBUG
    # ==================================================

    print()
    print("==============================================")
    print("GROQ ANSWER GENERATION")
    print("==============================================")
    print(f"Mode: {mode}")
    print(f"Question: {question}")
    print(f"Context characters: {len(context)}")
    print(
        f"Conversation characters: "
        f"{len(conversation_history)}"
    )
    print("==============================================")
    print()

    # ==================================================
    # CASUAL CHAT
    # ==================================================

    if mode == "casual":

        prompt = f"""
You are a friendly enterprise AI assistant.

The user is having a normal conversation.

Do not use document retrieval.

Do not mention documents, retrieval, context,
sources, chunks, or evidence unless the user
specifically asks about them.

Previous Conversation:
{conversation_history}

Current Message:
{question}

Respond naturally and concisely.
"""

        response = groq_client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a friendly and helpful "
                        "AI assistant."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4
        )

        answer = (
            response.choices[0]
            .message
            .content
            .strip()
        )

        print()
        print("GROQ CASUAL ANSWER:")
        print("----------------------------------------------")
        print(answer)
        print("----------------------------------------------")
        print()

        return answer

    # ==================================================
    # DOCUMENT OVERVIEW
    # ==================================================

    if mode == "document_overview":

        prompt = f"""
You are an enterprise document knowledge assistant.

The user is asking a BROAD or DOCUMENT-LEVEL question.

The provided context contains multiple sections
retrieved from different parts of the document.

Your job is to synthesize the relevant information
across those sections and give the user a useful,
well-organized answer.

IMPORTANT:

1. Use ONLY information supported by the provided
   document context.

2. Do NOT invent facts.

3. The context may contain information from different
   sections of the same document.

4. Combine related information from those sections
   instead of focusing only on one chunk.

5. For broad questions such as:
   - main principles
   - key concepts
   - main topics
   - important points
   - overview
   - what the document discusses

   provide a structured synthesis of the relevant
   information found across the supplied context.

6. Do not simply say that the context contains several
   sections.

7. Do not mention chunks, vector search, embeddings,
   reranking, retrieval, evidence gates, or internal
   system implementation.

8. If the context contains enough information to answer
   the question, ANSWER THE QUESTION.

9. Only say:

"I don't have enough information in the provided documents."

   if the supplied context genuinely does not contain
   enough information to answer the question.

10. Conversation history is provided only to resolve
    references in follow-up questions.

Previous Conversation:
{conversation_history}

Relevant Document Context:
{context}

Current Question:
{question}

Return ONLY the answer.
"""

        print(
            "GROQ DOCUMENT OVERVIEW REQUEST START"
        )

        response = groq_client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an enterprise document "
                        "knowledge assistant. "
                        "Answer using only the supplied "
                        "document context. "
                        "Synthesize information across "
                        "multiple retrieved sections. "
                        "Do not invent information."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        answer = (
            response.choices[0]
            .message
            .content
            .strip()
        )

        print(
            "GROQ DOCUMENT OVERVIEW RESPONSE RECEIVED"
        )

        print()
        print("GROQ DOCUMENT OVERVIEW ANSWER:")
        print("----------------------------------------------")
        print(answer)
        print("----------------------------------------------")
        print()

        return answer

    # ==================================================
    # NORMAL DOCUMENT / RAG CHAT
    # ==================================================

    prompt = f"""
You are an enterprise knowledge assistant.

Answer the user's question using ONLY information
contained in the provided document context.

The document context contains retrieved passages
that are relevant to the user's question.

Rules:

1. Use only information supported by the context.

2. Do not invent facts.

3. Answer the user's actual question directly.

4. Conversation history is provided only to understand
   references and follow-up questions.

5. If the answer is clearly present in the context,
   answer it.

6. If multiple context sections are relevant, combine
   them into one coherent answer.

7. Do not mention internal retrieval details such as:
   - vector search
   - embeddings
   - reranking
   - chunks
   - evidence gates

8. If the answer genuinely cannot be found in the
   provided context, say exactly:

"I don't have enough information in the provided documents."

Previous Conversation:
{conversation_history}

Relevant Document Context:
{context}

Current Question:
{question}

Return ONLY the answer.
"""

    print(
        "GROQ DOCUMENT REQUEST START"
    )

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an enterprise knowledge "
                    "assistant. "
                    "Use the supplied document context "
                    "to answer questions. "
                    "Do not invent information."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    answer = (
        response.choices[0]
        .message
        .content
        .strip()
    )

    print(
        "GROQ DOCUMENT RESPONSE RECEIVED"
    )

    print()
    print("GROQ DOCUMENT ANSWER:")
    print("----------------------------------------------")
    print(answer)
    print("----------------------------------------------")
    print()

    return answer


# ======================================================
# GEMINI ERROR HELPERS
# ======================================================

def _is_gemini_quota_error(
    error: Exception
) -> bool:

    error_text = str(error).upper()

    return (
        "429" in error_text
        or "RESOURCE_EXHAUSTED" in error_text
        or "QUOTA" in error_text
    )


def _is_gemini_temporary_error(
    error: Exception
) -> bool:

    error_text = str(error).upper()

    return (
        "500" in error_text
        or "502" in error_text
        or "503" in error_text
        or "504" in error_text
        or "UNAVAILABLE" in error_text
        or "INTERNAL" in error_text
    )


# ======================================================
# GEMINI SUMMARY REQUEST
# ======================================================

def _generate_gemini_summary(
    prompt: str
) -> str:

    max_attempts = 3

    for attempt in range(
        1,
        max_attempts + 1
    ):

        print(
            f"GEMINI REQUEST ATTEMPT "
            f"{attempt}/{max_attempts}"
        )

        try:

            response = (
                gemini_client
                .models
                .generate_content(
                    model=GEMINI_MODEL_NAME,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=4096
                    )
                )
            )

            print(
                "GEMINI RESPONSE RECEIVED"
            )

            if not response.text:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text.strip()

        except Exception as error:

            print()
            print(
                "GEMINI REQUEST ERROR:"
            )
            print(error)
            print()

            # ------------------------------------------
            # QUOTA ERROR
            # ------------------------------------------

            if _is_gemini_quota_error(error):

                raise RuntimeError(
                    "Gemini API quota/rate limit was "
                    "exhausted. Please wait for the quota "
                    "to reset or use a different Gemini "
                    "model/project."
                ) from error

            # ------------------------------------------
            # TEMPORARY ERROR
            # ------------------------------------------

            if _is_gemini_temporary_error(error):

                if attempt < max_attempts:

                    wait_seconds = (
                        2 ** (attempt - 1)
                    )

                    print(
                        f"Temporary Gemini error. "
                        f"Retrying in "
                        f"{wait_seconds} seconds..."
                    )

                    time.sleep(
                        wait_seconds
                    )

                    continue

            # ------------------------------------------
            # UNKNOWN ERROR
            # ------------------------------------------

            raise RuntimeError(
                f"Gemini document summary failed: "
                f"{error}"
            ) from error

    raise RuntimeError(
        "Gemini document summary failed after "
        "all retry attempts."
    )


# ======================================================
# DOCUMENT SUMMARY
# ======================================================

def generate_document_summary(
    text: str,
    filename: str
) -> str:

    """
    Generate a detailed technical document summary
    using Gemini.

    Groq:
        - Query rewriting
        - RAG answer generation
        - Casual conversation

    Gemini:
        - Document summarization
    """

    print()
    print(
        "=============================================="
    )
    print(
        "GEMINI DOCUMENT SUMMARY"
    )
    print(
        "=============================================="
    )
    print(
        f"Document: {filename}"
    )
    print(
        f"Input characters: {len(text)}"
    )
    print(
        f"Model: {GEMINI_MODEL_NAME}"
    )
    print(
        "=============================================="
    )
    print()

    prompt = f"""
You are an enterprise document summarization assistant.

Create a clear, accurate and useful technical summary
of the provided document content.

Document filename:
{filename}

Document content:
{text}

Instructions:

1. Summarize ONLY information contained in the content.

2. Do not invent facts.

3. Preserve important:
   - class names
   - method names
   - function names
   - properties
   - parameters
   - return values
   - relationships
   - workflows
   - technical details
   - examples
   - important values

4. Use clear headings and bullet points.

5. If the document contains source code or technical
   classes, explain each class and its important methods.

6. Explain relationships between components when supported.

7. Keep important implementation details.

8. Make the summary useful to someone who has not read
   the original document.

9. Do not introduce information that is not present
   in the provided content.

10. Return ONLY the summary.

Do not discuss these instructions.
"""

    print(
        "GEMINI REQUEST START"
    )

    summary = _generate_gemini_summary(
        prompt
    )

    print()
    print(
        "GEMINI RESPONSE TEXT:"
    )
    print(
        "----------------------------------------------"
    )
    print(summary)
    print(
        "----------------------------------------------"
    )
    print()

    return summary