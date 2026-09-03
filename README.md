# Enterprise AI Knowledge Assistant

An enterprise-focused Retrieval-Augmented Generation (RAG) application that allows authenticated users to upload PDF documents and ask natural-language questions against their private knowledge base.

The system combines document processing, embeddings, vector search, reranking, evidence validation, conversational context, and LLM generation to produce grounded answers based on uploaded documents.

---

## 🚀 Overview

The Enterprise AI Knowledge Assistant is designed to provide a private, document-grounded AI experience.

Users can:

- Create an account and securely log in
- Upload PDF documents
- Process and index documents
- Store document chunks and embeddings
- Ask questions about uploaded documents
- Continue conversations with contextual follow-up questions
- Search documents using semantic similarity
- Retrieve relevant document chunks using vector search
- Rerank retrieved chunks for improved relevance
- Validate whether sufficient evidence exists before generating an answer
- Receive source attribution for generated responses
- Create, view, and delete conversations
- Maintain separate user-scoped document knowledge bases

---

## ✨ Features

### 🔐 Authentication

- User registration and login
- JWT-based authentication
- Password hashing using bcrypt
- Protected API endpoints
- User-scoped data access

### 📄 Document Management

- PDF upload
- PDF text extraction
- Text chunking
- Document metadata storage
- Embedding generation
- Vector storage using PostgreSQL + pgvector
- Document listing
- Document deletion
- Document summaries

### 🧠 Retrieval-Augmented Generation

The application implements an end-to-end RAG pipeline:

```text
PDF
 ↓
Text Extraction
 ↓
Chunking
 ↓
Embedding Generation
 ↓
PostgreSQL + pgvector
 ↓
Semantic Vector Search
 ↓
Candidate Chunks
 ↓
Cross-Encoder Reranking
 ↓
Evidence Validation
 ↓
Context Construction
 ↓
LLM Generation
 ↓
Grounded Answer