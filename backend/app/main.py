from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.document import router as document_router
from app.api.conversations import router as conversation_router

from app.models.user import User
from app.models.document import Document
from app.models.chunk import Chunk
from app.models.conversation import Conversation
from app.models.message import Message


# ======================================================
# FASTAPI APP
# ======================================================

app = FastAPI(
    title="Enterprise AI Knowledge Assistant"
)


# ======================================================
# CORS
# ======================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ======================================================
# API ROUTERS
# ======================================================

app.include_router(auth_router)
app.include_router(document_router)
app.include_router(conversation_router)


# ======================================================
# ROOT
# ======================================================

@app.get("/")
def root():
    return {
        "message": "Enterprise AI Knowledge Assistant Running"
    }


# ======================================================
# HEALTH CHECK
# ======================================================

@app.get("/health")
def health():
    return {
        "status": "ok"
    }