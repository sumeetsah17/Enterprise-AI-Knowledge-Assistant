import { useEffect, useState } from "react";

import {
  MessageSquare,
  Plus,
  Search,
  Settings,
  User,
  Send,
  Sparkles,
  Trash2,
  LogOut,
  Lock,
  Mail,
  FileText,
  Upload,
  Eye,
  X,
} from "lucide-react";

import ReactMarkdown from "react-markdown";

import "./App.css";

import {
  loginUser,
  getConversations,
  createConversation,
  attachConversationDocument,
  getConversation,
  deleteConversation,
  sendChatMessage,
  getDocuments,
  uploadDocument,
  getDocumentSummary,
  deleteDocument,
} from "./api";


// ==================================================
// LOGIN PAGE
// ==================================================

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(event) {
    event.preventDefault();

    setError("");

    if (!email.trim() || !password.trim()) {
      setError("Please enter your email and password.");
      return;
    }

    try {
      setLoading(true);

      const data = await loginUser(
        email,
        password
      );

      /*
       * FastAPI normally returns:
       *
       * {
       *   "access_token": "...",
       *   "token_type": "bearer"
       * }
       */

      const token =
        data.access_token || data.token;

      if (!token) {
        throw new Error(
          "Login succeeded but no access token was returned."
        );
      }

      localStorage.setItem(
        "token",
        token
      );

      localStorage.setItem(
        "userEmail",
        email
      );

      onLogin(token);

    } catch (error) {
      console.error(error);

      setError(
        error.message ||
        "Unable to login."
      );
    } finally {
      setLoading(false);
    }
  }


  return (
    <div className="login-page">

      <div className="login-card">

        {/* Logo */}

        <div className="login-logo">
          <Sparkles size={27} />
        </div>

        <h1>
          Enterprise AI
        </h1>

        <p className="login-subtitle">
          Knowledge Assistant
        </p>


        <div className="login-welcome">
          <h2>
            Welcome back
          </h2>

          <p>
            Sign in to access your
            enterprise knowledge base.
          </p>
        </div>


        {/* Error */}

        {error && (
          <div className="login-error">
            {error}
          </div>
        )}


        {/* Form */}

        <form onSubmit={handleLogin}>

          <label>
            Email
          </label>

          <div className="login-input">

            <Mail size={17} />

            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              autoComplete="email"
            />

          </div>


          <label>
            Password
          </label>

          <div className="login-input">

            <Lock size={17} />

            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              autoComplete="current-password"
            />

          </div>


          <button
            className="login-button"
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Signing in..."
              : "Sign in"}
          </button>

        </form>


        <div className="login-footer">
          Secure enterprise knowledge access
        </div>

      </div>

    </div>
  );
}


// ==================================================
// MAIN APP
// ==================================================

function Dashboard({ token, onLogout }) {

  const [conversations, setConversations] =
    useState([]);

  const [selectedConversation, setSelectedConversation] =
    useState(null);

  const [messages, setMessages] =
    useState([]);

  const [searchText, setSearchText] =
    useState("");

  const [question, setQuestion] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [loadingConversations, setLoadingConversations] =
    useState(true);

  const [error, setError] =
    useState("");

  const [documents, setDocuments] =
    useState([]);

  const [loadingDocuments, setLoadingDocuments] =
    useState(true);

  const [uploadingDocument, setUploadingDocument] =
    useState(false);

  const [selectedDocument, setSelectedDocument] =
    useState(null);
  
  const [lastUploadedDocument, setLastUploadedDocument] =
  useState(null);

  const [documentSummary, setDocumentSummary] =
    useState("");

  const [loadingSummary, setLoadingSummary] =
    useState(false);


  // ================================================
  // LOAD CONVERSATIONS
  // ================================================

  useEffect(() => {

    async function load() {

      try {

        setLoadingConversations(true);

        setError("");

        const data =
          await getConversations(token);

        setConversations(data);

      } catch (error) {

        console.error(error);

        setError(
          error.message ||
          "Unable to load conversations."
        );

      } finally {

        setLoadingConversations(false);

      }
    }

    load();

  }, [token]);


  // ================================================
  // LOAD DOCUMENTS
  // ================================================

  useEffect(() => {

    async function loadDocuments() {

      try {

        setLoadingDocuments(true);

        const data = await getDocuments(token);

        setDocuments(Array.isArray(data) ? data : []);

      } catch (error) {

        console.error(error);

        setError(
          error.message ||
          "Unable to load documents."
        );

      } finally {

        setLoadingDocuments(false);

      }
    }

    loadDocuments();

  }, [token]);


  // ================================================
  // UPLOAD DOCUMENT
  // ================================================

  async function handleUploadDocument(event) {

    const file = event.target.files?.[0];

    event.target.value = "";

    if (!file) {
      return;
    }

    if (file.type !== "application/pdf" &&
        !file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please upload a PDF file.");
      return;
    }

    try {

      setUploadingDocument(true);
      setError("");

      const uploaded = await uploadDocument(
        token,
        file
      );

      const refreshed = await getDocuments(token);

      const uploadedDocument =
        Array.isArray(refreshed)
          ? refreshed.find(
              document => document.id === uploaded.id
            ) || uploaded
          : uploaded;

      setDocuments(
        Array.isArray(refreshed)
          ? refreshed
          : [uploadedDocument, ...documents]
      );

      setLastUploadedDocument(uploadedDocument);

      // If a conversation is currently open, automatically attach
      // the newly uploaded PDF to that conversation.
      if (selectedConversation?.id) {
        const updatedConversation =
          await attachConversationDocument(
            token,
            selectedConversation.id,
            uploadedDocument.id
          );

        setSelectedConversation(updatedConversation);

        setConversations(previous =>
          previous.map(conversation =>
            conversation.id === updatedConversation.id
              ? updatedConversation
              : conversation
          )
        );
      }

    } catch (error) {

      console.error(error);

      setError(
        error.message ||
        "Unable to upload document."
      );

    } finally {

      setUploadingDocument(false);

    }
  }


  // ================================================
  // ATTACH EXISTING DOCUMENT TO CURRENT CONVERSATION
  // ================================================

  async function handleAttachDocument(document) {

    if (!selectedConversation?.id) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      const updatedConversation =
        await attachConversationDocument(
          token,
          selectedConversation.id,
          document.id
        );

      setSelectedConversation(updatedConversation);

      setConversations(previous =>
        previous.map(conversation =>
          conversation.id === updatedConversation.id
            ? updatedConversation
            : conversation
        )
      );

      setLastUploadedDocument(null);

    } catch (error) {
      console.error(error);
      setError(
        error.message ||
        "Unable to attach document to conversation."
      );
    } finally {
      setLoading(false);
    }
  }


  // ================================================
  // OPEN DOCUMENT SUMMARY
  // ================================================

  async function handleOpenDocument(document) {

    try {

      setSelectedDocument(document);
      setDocumentSummary("");
      setLoadingSummary(true);
      setError("");

      const data = await getDocumentSummary(
        token,
        document.id
      );

      setDocumentSummary(data.summary || "");

    } catch (error) {

      console.error(error);

      setError(
        error.message ||
        "Unable to generate document summary."
      );

    } finally {

      setLoadingSummary(false);

    }
  }


  // ================================================
  // CLOSE DOCUMENT SUMMARY
  // ================================================

  function handleCloseDocument() {

    setSelectedDocument(null);
    setDocumentSummary("");
    setLoadingSummary(false);

  }


  // ================================================
  // DELETE DOCUMENT
  // ================================================

  async function handleDeleteDocument(
    event,
    documentId
  ) {

    event.stopPropagation();

    const confirmed = window.confirm(
      "Are you sure you want to delete this document? This will also delete its indexed chunks."
    );

    if (!confirmed) {
      return;
    }

    try {

      setError("");

      await deleteDocument(
        token,
        documentId
      );

      setDocuments(previous =>
        previous.filter(
          document => document.id !== documentId
        )
      );

      if (selectedDocument?.id === documentId) {
        handleCloseDocument();
      }

    } catch (error) {

      console.error(error);

      setError(
        error.message ||
        "Unable to delete document."
      );

    }
  }


  // ================================================
  // OPEN CONVERSATION
  // ================================================

  async function openConversation(
    conversationId
  ) {

    try {

      setLoading(true);

      setError("");

      const data =
        await getConversation(
          token,
          conversationId
        );

      setSelectedConversation(data);

      setMessages(
        data.messages || []
      );

    } catch (error) {

      console.error(error);

      setError(
        error.message ||
        "Unable to load conversation."
      );

    } finally {

      setLoading(false);

    }
  }


  // ================================================
  // NEW CONVERSATION
  // ================================================

  async function handleNewConversation() {

    try {

      setLoading(true);

      setError("");

      const data =
        await createConversation(token);

      setConversations(
        previous => [
          data,
          ...previous,
        ]
      );

      setSelectedConversation(data);

      setMessages([]);

    } catch (error) {

      console.error(error);

      setError(
        error.message ||
        "Unable to create conversation."
      );

    } finally {

      setLoading(false);

    }
  }


  // ================================================
  // DELETE CONVERSATION
  // ================================================

  async function handleDeleteConversation(
    event,
    conversationId
  ) {

    event.stopPropagation();

    const confirmed =
      window.confirm(
        "Are you sure you want to delete this conversation?"
      );

    if (!confirmed) {
      return;
    }

    try {

      setError("");

      await deleteConversation(
        token,
        conversationId
      );

      setConversations(
        previous =>
          previous.filter(
            conversation =>
              conversation.id !==
              conversationId
          )
      );

      if (
        selectedConversation?.id ===
        conversationId
      ) {

        setSelectedConversation(null);

        setMessages([]);

      }

    } catch (error) {

      console.error(error);

      setError(
        error.message ||
        "Unable to delete conversation."
      );
    }
  }

  // ================================================
  // SEND CHAT MESSAGE
  // ================================================

  async function handleSendMessage() {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      return;
    }

    if (!selectedConversation) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      // --------------------------------------------
      // Add user's message immediately to the UI
      // --------------------------------------------

      const temporaryUserMessage = {
        id: `temp-user-${Date.now()}`,
        role: "user",
        content: trimmedQuestion,
      };

      setMessages((previous) => [
        ...previous,
        temporaryUserMessage,
      ]);

      // Clear input
      setQuestion("");

      // --------------------------------------------
      // Call FastAPI RAG endpoint
      // --------------------------------------------

      const data = await sendChatMessage(
        token,
        selectedConversation.id,
        trimmedQuestion
      );

      // --------------------------------------------
      // Add AI response
      // --------------------------------------------

      const aiMessage = {
        id: `temp-ai-${Date.now()}`,
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
      };

      setMessages((previous) => [
        ...previous,
        aiMessage,
      ]);

    } catch (error) {
      console.error(error);

      setError(
        error.message ||
        "Unable to get an answer from Enterprise AI."
      );

    } finally {
      setLoading(false);
    }
  }


  // ================================================
  // LOGOUT
  // ================================================

  function handleLogout() {

    localStorage.removeItem(
      "token"
    );

    localStorage.removeItem(
      "userEmail"
    );

    onLogout();

  }


  // ================================================
  // FILTER
  // ================================================

  const filteredConversations =
    conversations.filter(
      conversation =>
        conversation.title
          ?.toLowerCase()
          .includes(
            searchText.toLowerCase()
          )
    );


  // ================================================
  // UI
  // ================================================

  return (

    <div className="app">


      {/* ==========================================
          SIDEBAR
      ========================================== */}

      <aside className="sidebar">

        <div className="logo">

          <div className="logo-icon">
            <Sparkles size={20} />
          </div>

          <div>

            <h1>
              Enterprise AI
            </h1>

            <span>
              Knowledge Assistant
            </span>

          </div>

        </div>


        <button
          className="new-chat"
          onClick={
            handleNewConversation
          }
        >

          <Plus size={18} />

          New conversation

        </button>


        <div className="conversation-search">

          <Search size={16} />

          <input
            type="text"
            placeholder="Search conversations..."
            value={searchText}
            onChange={(event) =>
              setSearchText(
                event.target.value
              )
            }
          />

        </div>


        <div className="conversation-section">

          <p className="section-title">
            CONVERSATIONS
          </p>


          {loadingConversations && (

            <p className="sidebar-message">
              Loading conversations...
            </p>

          )}


          {!loadingConversations &&
            filteredConversations.length === 0 && (

              <p className="sidebar-message">
                No conversations yet.
              </p>

            )}


          {filteredConversations.map(
            conversation => (

              <button
                key={conversation.id}
                className={`conversation ${selectedConversation?.id ===
                  conversation.id
                  ? "active"
                  : ""
                  }`}
                onClick={() =>
                  openConversation(
                    conversation.id
                  )
                }
              >

                <MessageSquare size={17} />

                <div className="conversation-info">

                  <span>
                    {
                      conversation.title ||
                      "New Conversation"
                    }
                  </span>

                  <small>
                    Conversation #
                    {conversation.id}
                  </small>

                </div>


                <span
                  className="delete-icon"
                  onClick={(event) =>
                    handleDeleteConversation(
                      event,
                      conversation.id
                    )
                  }
                >

                  <Trash2 size={14} />

                </span>

              </button>

            )
          )}

        </div>


        {/* ==========================================
            DOCUMENTS
        ========================================== */}

        <div className="documents-section">

          <div className="documents-header">

            <p className="section-title">
              DOCUMENTS
            </p>

            <label
              className="document-upload-button"
              title="Upload PDF"
            >

              <Upload size={14} />

              <input
                id="document-upload-input"
                type="file"
                accept="application/pdf,.pdf"
                onChange={handleUploadDocument}
                disabled={uploadingDocument}
                hidden
              />

            </label>

          </div>

          {uploadingDocument && (
            <p className="sidebar-message">
              Uploading and indexing PDF...
            </p>
          )}

          {!uploadingDocument && loadingDocuments && (
            <p className="sidebar-message">
              Loading documents...
            </p>
          )}

          {!loadingDocuments &&
            !uploadingDocument &&
            documents.length === 0 && (
              <p className="sidebar-message">
                No documents uploaded yet.
              </p>
            )}

          {!loadingDocuments &&
            documents.map(document => (
              <div
                className={`document-item ${selectedDocument?.id === document.id ? "active" : ""}`}
                key={document.id}
                onClick={() => handleOpenDocument(document)}
              >

                <FileText size={16} />

                <div className="document-info">
                  <span title={document.filename}>
                    {document.filename || "Document"}
                  </span>
                  <small>
                    Document #{document.id}
                  </small>
                </div>

                <button
                  className="document-delete-button"
                  title="Delete document"
                  onClick={(event) =>
                    handleDeleteDocument(
                      event,
                      document.id
                    )
                  }
                >
                  <Trash2 size={13} />
                </button>

              </div>
            ))}

        </div>


        <div className="sidebar-bottom">

          <button className="sidebar-button">

            <Settings size={17} />

            Settings

          </button>


          <button
            className="sidebar-button"
            onClick={handleLogout}
          >

            <LogOut size={17} />

            Logout

          </button>


          <div className="user-profile">

            <div className="avatar">
              <User size={17} />
            </div>

            <div className="user-info">

              <strong>
                {localStorage.getItem(
                  "userEmail"
                ) || "Sumeet"}
              </strong>

              <span>
                Online
              </span>

            </div>

          </div>

        </div>

      </aside>


      {/* ==========================================
          CHAT
      ========================================== */}

      <main className="chat-area">


        <header className="chat-header">

          <div>

            <h2>
              {
                selectedConversation?.title ||
                "Enterprise AI Assistant"
              }
            </h2>

            <span>
              Ask questions about your knowledge base
            </span>

          </div>


          <div className="header-status">

            <div className="status-dot"></div>

            AI Online

          </div>

        </header>


        {error && (

          <div className="app-error">
            {error}
          </div>

        )}


        <div className="messages">


          {!selectedConversation && (

            <div className="empty-state">

              <div className="empty-icon">
                <Sparkles size={30} />
              </div>

              <h3>
                Welcome to Enterprise AI
              </h3>

              <p>
                Select a conversation or
                start a new one.
              </p>

            </div>

          )}


          {selectedConversation &&
            messages.length === 0 && (
              <div
                className="empty-state"
                style={{
                  width: "min(860px, 94%)",
                  margin: "auto",
                  padding: "34px 20px",
                  textAlign: "center"
                }}
              >
                {(() => {
                  const conversationDocument =
                    selectedConversation?.document_id
                      ? documents.find(
                          document =>
                            document.id ===
                            selectedConversation.document_id
                        )
                      : null;

                  if (conversationDocument) {
                    return (
                      <>
                        <div
                          style={{
                            width: "100%",
                            maxWidth: "680px",
                            margin: "0 auto 26px",
                            padding: "22px",
                            display: "flex",
                            alignItems: "center",
                            gap: "18px",
                            textAlign: "left",
                            borderRadius: "22px",
                            border: "1px solid rgba(124,58,237,.15)",
                            background: "linear-gradient(135deg, rgba(124,58,237,.09), rgba(255,255,255,.92))",
                            boxShadow: "0 16px 45px rgba(15,23,42,.08)"
                          }}
                        >
                          <div
                            style={{
                              position: "relative",
                              width: "68px",
                              height: "80px",
                              minWidth: "68px",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              borderRadius: "14px",
                              background: "#fff",
                              color: "#ef4444",
                              border: "1px solid rgba(239,68,68,.14)",
                              boxShadow: "0 7px 20px rgba(15,23,42,.08)"
                            }}
                          >
                            <FileText size={34} />
                            <span
                              style={{
                                position: "absolute",
                                right: "-7px",
                                bottom: "-7px",
                                padding: "3px 6px",
                                borderRadius: "5px",
                                background: "#ef4444",
                                color: "#fff",
                                fontSize: "9px",
                                fontWeight: 800
                              }}
                            >
                              PDF
                            </span>
                          </div>

                          <div style={{ minWidth: 0, flex: 1 }}>
                            <div
                              style={{
                                fontSize: "11px",
                                fontWeight: 700,
                                color: "#7c3aed",
                                textTransform: "uppercase",
                                letterSpacing: ".08em",
                                marginBottom: "5px"
                              }}
                            >
                              Document attached
                            </div>

                            <h3
                              style={{
                                margin: 0,
                                fontSize: "17px",
                                color: "#171923",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap"
                              }}
                              title={conversationDocument.filename}
                            >
                              {conversationDocument.filename || "Document"}
                            </h3>

                            <p
                              style={{
                                margin: "6px 0 9px",
                                fontSize: "12px",
                                color: "#7b8191"
                              }}
                            >
                              Document #{conversationDocument.id}
                            </p>

                            <div
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "7px",
                                color: "#15803d",
                                fontSize: "11px",
                                fontWeight: 650
                              }}
                            >
                              <span
                                style={{
                                  width: "7px",
                                  height: "7px",
                                  borderRadius: "50%",
                                  background: "#22c55e"
                                }}
                              />
                              Ready to answer questions
                            </div>
                          </div>

                          <Sparkles
                            size={21}
                            color="#7c3aed"
                          />
                        </div>

                        <div className="empty-icon" style={{ marginBottom: "14px" }}>
                          <Sparkles size={28} />
                        </div>

                        <h3 style={{ marginBottom: "8px" }}>
                          Ask anything about your document
                        </h3>

                        <p
                          style={{
                            margin: "0 auto",
                            maxWidth: "520px",
                            color: "#7b8191"
                          }}
                        >
                          Your conversation is now connected to this PDF.
                          Ask a question below to get started.
                        </p>
                      </>
                    );
                  }

                  return (
                    <>
                      <div
                        style={{
                          width: "74px",
                          height: "74px",
                          margin: "0 auto 18px",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          borderRadius: "22px",
                          background: "linear-gradient(135deg,#7c3aed,#4f46e5)",
                          color: "#fff",
                          boxShadow: "0 14px 32px rgba(79,70,229,.22)"
                        }}
                      >
                        <FileText size={32} />
                      </div>

                      <h3 style={{ marginBottom: "8px" }}>
                        Choose a document to get started
                      </h3>

                      <p
                        style={{
                          margin: "0 auto 22px",
                          maxWidth: "520px",
                          color: "#7b8191"
                        }}
                      >
                        Reuse a PDF from your library or upload a new one.
                        You won't need to upload an existing document again.
                      </p>

                      {documents.length > 0 && (
                        <div
                          style={{
                            width: "100%",
                            maxWidth: "760px",
                            margin: "0 auto 20px",
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))",
                            gap: "12px",
                            textAlign: "left"
                          }}
                        >
                          {documents.map(document => (
                            <button
                              key={document.id}
                              type="button"
                              onClick={() => handleAttachDocument(document)}
                              disabled={loading || uploadingDocument}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "12px",
                                width: "100%",
                                padding: "14px",
                                borderRadius: "15px",
                                border: "1px solid #e6e8ef",
                                background: "#fff",
                                cursor: "pointer",
                                textAlign: "left",
                                boxShadow: "0 5px 16px rgba(15,23,42,.04)",
                                opacity: loading ? .65 : 1
                              }}
                            >
                              <span
                                style={{
                                  width: "40px",
                                  height: "46px",
                                  minWidth: "40px",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  borderRadius: "9px",
                                  background: "#fef2f2",
                                  color: "#ef4444"
                                }}
                              >
                                <FileText size={21} />
                              </span>

                              <span style={{ minWidth: 0 }}>
                                <strong
                                  style={{
                                    display: "block",
                                    fontSize: "13px",
                                    color: "#20222d",
                                    overflow: "hidden",
                                    textOverflow: "ellipsis",
                                    whiteSpace: "nowrap"
                                  }}
                                >
                                  {document.filename || "Document"}
                                </strong>
                                <small
                                  style={{
                                    display: "block",
                                    marginTop: "4px",
                                    color: "#8b91a1"
                                  }}
                                >
                                  Document #{document.id} · Use this PDF
                                </small>
                              </span>
                            </button>
                          ))}
                        </div>
                      )}

                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: "12px",
                          marginTop: "8px"
                        }}
                      >
                        <span style={{ color: "#a0a5b2", fontSize: "12px" }}>
                          or
                        </span>

                        <label
                          htmlFor="new-conversation-upload-input"
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "8px",
                            padding: "11px 17px",
                            borderRadius: "11px",
                            background: "#171923",
                            color: "#fff",
                            fontSize: "13px",
                            fontWeight: 650,
                            cursor: "pointer",
                            boxShadow: "0 7px 18px rgba(15,23,42,.14)"
                          }}
                        >
                          <Upload size={16} />
                          {uploadingDocument ? "Uploading..." : "Upload new PDF"}
                        </label>

                        <input
                          id="new-conversation-upload-input"
                          type="file"
                          accept="application/pdf,.pdf"
                          onChange={handleUploadDocument}
                          disabled={uploadingDocument}
                          hidden
                        />
                      </div>
                    </>
                  );
                })()}
              </div>
            )}

          {messages.map(message => (

            <div
              key={message.id}
              className="message"
            >

              <div
                className={`message-avatar ${message.role === "user"
                  ? "user-avatar"
                  : "ai-avatar"
                  }`}
              >

                {message.role === "user"
                  ? "S"
                  : <Sparkles size={16} />}

              </div>


              <div className="message-content">

                <div className="message-name">

                  {message.role === "user"
                    ? "You"
                    : "Enterprise AI"}

                </div>


                <div
                  className={`message-bubble ${message.role === "user"
                      ? "user-bubble"
                      : "ai-bubble"
                    }`}
                >
                  {message.role === "assistant" ? (
                    <>
                      <ReactMarkdown>
                        {message.content}
                      </ReactMarkdown>

                      {message.sources &&
                        message.sources.length > 0 && (
                          <div className="sources-section">

                            <div className="sources-title">
                              <FileText size={14} />
                              <span>SOURCES</span>
                            </div>

                            <div className="sources-list">
                              {message.sources.map((source) => (
                                <div
                                  className="source-card"
                                  key={`${source.document_id}-${source.chunk_id}`}
                                >
                                  <div className="source-icon">
                                    <FileText size={17} />
                                  </div>

                                  <div className="source-info">
                                    <strong>
                                      {source.filename
                                        ? source.filename
                                          .replace(/\+/g, " ")
                                          .replace(".pdf", "")
                                        : "Document"}
                                    </strong>

                                    <span>
                                      Chunk {source.chunk_id}
                                      {" · "}
                                      Document {source.document_id}
                                    </span>
                                  </div>
                                </div>
                              ))}
                            </div>

                          </div>
                        )}
                    </>
                  ) : (
                    message.content
                  )}
                </div>

              </div>

            </div>

          ))}


          {loading &&
            selectedConversation && (

              <div className="message">

                <div className="message-avatar ai-avatar">
                  <Sparkles size={16} />
                </div>

                <div className="message-content">

                  <div className="message-name">
                    Enterprise AI
                  </div>

                  <div className="message-bubble ai-bubble">
                    Thinking...
                  </div>

                </div>

              </div>

            )}

        </div>


        {selectedDocument && (
          <div className="document-modal-overlay">

            <div className="document-modal">

              <div className="document-modal-header">

                <div>
                  <div className="document-modal-title">
                    <FileText size={18} />
                    <strong>
                      {selectedDocument.filename || "Document"}
                    </strong>
                  </div>

                  <span>
                    Document #{selectedDocument.id}
                  </span>
                </div>

                <button
                  className="document-modal-close"
                  onClick={handleCloseDocument}
                  title="Close"
                >
                  <X size={18} />
                </button>

              </div>

              <div className="document-modal-content">

                {loadingSummary ? (
                  <div className="document-summary-loading">
                    <Sparkles size={22} />
                    <p>
                      Generating summary with Gemini...
                    </p>
                  </div>
                ) : documentSummary ? (
                  <ReactMarkdown>
                    {documentSummary}
                  </ReactMarkdown>
                ) : (
                  <p>
                    No summary is available for this document.
                  </p>
                )}

              </div>

            </div>

          </div>
        )}


        <div className="chat-input-container">

          <div className="chat-input">

            <input
              type="text"
              placeholder={
                selectedConversation
                  ? "Ask anything about your documents..."
                  : "Select a conversation first..."
              }
              value={question}
              disabled={
                !selectedConversation ||
                loading
              }
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey
                ) {
                  event.preventDefault();

                  handleSendMessage();
                }
              }}
            />


            <button
              className="send-button"
              disabled={
                !selectedConversation ||
                !question.trim() ||
                loading
              }
              onClick={handleSendMessage}
            >
              <Send size={18} />
            </button>

          </div>


          <div className="input-hint">

            Enterprise AI can answer questions
            using your uploaded documents.

          </div>

        </div>

      </main>

    </div>
  );
}


// ==================================================
// ROOT
// ==================================================

function App() {

  const [token, setToken] =
    useState(
      localStorage.getItem("token")
    );


  if (!token) {

    return (
      <LoginPage
        onLogin={setToken}
      />
    );

  }


  return (
    <Dashboard
      token={token}
      onLogout={() => setToken(null)}
    />
  );
}


export default App;