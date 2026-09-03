const API_BASE_URL = "http://localhost:8000";

// ======================================================
// HELPER
// ======================================================

async function parseResponse(response, defaultMessage) {
  let data = null;

  try {
    data = await response.json();
  } catch {
    // Response was not JSON
  }

  if (!response.ok) {
    throw new Error(
      data?.detail ||
      data?.message ||
      defaultMessage
    );
  }

  return data;
}


// ======================================================
// AUTH
// ======================================================

export async function loginUser(email, password) {
  const response = await fetch(
    `${API_BASE_URL}/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
      }),
    }
  );

  return parseResponse(
    response,
    "Login failed."
  );
}


// ======================================================
// CONVERSATIONS
// ======================================================

export async function getConversations(token) {
  const response = await fetch(
    `${API_BASE_URL}/conversations/`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return parseResponse(
    response,
    "Failed to load conversations."
  );
}


export async function createConversation(token) {
  const response = await fetch(
    `${API_BASE_URL}/conversations/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({}),
    }
  );

  return parseResponse(
    response,
    "Failed to create conversation."
  );
}


export async function getConversation(
  token,
  conversationId
) {
  const response = await fetch(
    `${API_BASE_URL}/conversations/${conversationId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return parseResponse(
    response,
    "Failed to load conversation."
  );
}


export async function deleteConversation(
  token,
  conversationId
) {
  const response = await fetch(
    `${API_BASE_URL}/conversations/${conversationId}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return parseResponse(
    response,
    "Failed to delete conversation."
  );
}


// ======================================================
// DOCUMENTS
// ======================================================

export async function getDocuments(token) {
  const response = await fetch(
    `${API_BASE_URL}/documents/`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return parseResponse(
    response,
    "Failed to load documents."
  );
}


export async function uploadDocument(
  token,
  file
) {
  const formData = new FormData();

  formData.append(
    "file",
    file
  );

  const response = await fetch(
    `${API_BASE_URL}/documents/upload`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    }
  );

  return parseResponse(
    response,
    "Failed to upload document."
  );
}


export async function getDocumentSummary(
  token,
  documentId
) {
  const response = await fetch(
    `${API_BASE_URL}/documents/${documentId}/summary`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return parseResponse(
    response,
    "Failed to generate document summary."
  );
}


export async function deleteDocument(
  token,
  documentId
) {
  const response = await fetch(
    `${API_BASE_URL}/documents/${documentId}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return parseResponse(
    response,
    "Failed to delete document."
  );
}


// ======================================================
// DOCUMENT SEARCH
// ======================================================

export async function searchDocuments(
  token,
  query,
  topK = 5
) {
  const response = await fetch(
    `${API_BASE_URL}/documents/search`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        query,
        top_k: topK,
      }),
    }
  );

  return parseResponse(
    response,
    "Document search failed."
  );
}


// ======================================================
// DOCUMENT CHAT / RAG
// ======================================================

export async function sendChatMessage(
  token,
  conversationId,
  question
) {
  const response = await fetch(
    `${API_BASE_URL}/documents/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        question,
      }),
    }
  );

  return parseResponse(
    response,
    "Failed to send message."
  );
}


// ======================================================
// DEFAULT EXPORT
// ======================================================

export default {
  loginUser,

  getConversations,
  createConversation,
  getConversation,
  deleteConversation,

  getDocuments,
  uploadDocument,
  getDocumentSummary,
  deleteDocument,

  searchDocuments,

  sendChatMessage,
};