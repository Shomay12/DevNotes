/**
 * DevNote API Client
 * Clean asynchronous HTTP interface to FastAPI backend
 * Supports token-based local network access & cross-edition configurations.
 */

const API = {
  // Retrieve token from query params or storage
  getAuthToken() {
    const urlParams = new URLSearchParams(window.location.search);
    const paramToken = urlParams.get("token");
    if (paramToken) {
      localStorage.setItem("devnote_auth_token", paramToken);
      return paramToken;
    }
    return localStorage.getItem("devnote_auth_token") || "";
  },

  setAuthToken(token) {
    if (token) {
      localStorage.setItem("devnote_auth_token", token.trim());
    } else {
      localStorage.removeItem("devnote_auth_token");
    }
  },

  // Base request handler with robust JSON & error handling
  async request(endpoint, options = {}) {
    const url = endpoint.startsWith("http") ? endpoint : endpoint;
    const defaultHeaders = {
      "Accept": "application/json",
    };

    const token = this.getAuthToken();
    if (token) {
      defaultHeaders["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData)) {
      defaultHeaders["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        if (response.status === 401) {
          window.dispatchEvent(new CustomEvent("devnote:auth_required"));
        }

        let errMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errData = await response.json();
          if (errData.detail) {
            errMessage = typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch (_) {}
        throw new Error(errMessage);
      }

      // Check if response is JSON or blob
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        return await response.json();
      }
      return response;
    } catch (err) {
      console.error(`API Error [${options.method || "GET"} ${endpoint}]:`, err);
      throw err;
    }
  },

  // Application & Edition Config
  async getConfig() {
    return this.request("/api/config");
  },

  // Notebooks
  async getNotebooks(params = {}) {
    const query = new URLSearchParams();
    if (params.query) query.append("query", params.query);
    if (params.tag) query.append("tag", params.tag);
    if (params.archived !== undefined) query.append("archived", params.archived);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return this.request(`/api/notebooks${qs}`);
  },

  async getRecentNotebooks(limit = 5) {
    return this.request(`/api/notebooks/recent?limit=${limit}`);
  },

  async getNotebook(id) {
    return this.request(`/api/notebooks/${id}`);
  },

  async createNotebook(data = {}) {
    return this.request("/api/notebooks", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateNotebook(id, data) {
    return this.request(`/api/notebooks/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  async autosaveContent(id, { blocks, title, tags, version }) {
    return this.request(`/api/notebooks/${id}/content`, {
      method: "PATCH",
      body: JSON.stringify({ blocks, title, tags, version }),
    });
  },

  async deleteNotebook(id) {
    return this.request(`/api/notebooks/${id}`, {
      method: "DELETE",
    });
  },

  // Code Execution
  async executeCode({ language, code, notebookId, blockId, timeout = 10.0 }) {
    return this.request("/api/execute", {
      method: "POST",
      body: JSON.stringify({
        language,
        code,
        notebook_id: notebookId,
        block_id: blockId,
        timeout,
      }),
    });
  },

  async getExecutionStatus(executionId) {
    return this.request(`/api/executions/${executionId}`);
  },

  async stopExecution(executionId) {
    return this.request(`/api/executions/${executionId}/stop`, {
      method: "POST",
    });
  },

  // PDF Export & Import
  async exportPDF(notebookId) {
    return this.request(`/api/notebooks/${notebookId}/export`, {
      method: "POST",
    });
  },

  async importPDF(formData) {
    return this.request("/api/notebooks/import", {
      method: "POST",
      body: formData,
    });
  },

  // Shared Canonical JSON Notebook Export & Import
  async exportJSON(notebookId) {
    return this.request(`/api/notebooks/${notebookId}/export-json`);
  },

  async importJSON(formData) {
    return this.request("/api/notebooks/import-json", {
      method: "POST",
      body: formData,
    });
  },

  // Developer Search Workspace
  async searchNotebooks(q, category = "all") {
    const query = new URLSearchParams({ q: q || "", category });
    return this.request(`/api/search/notebooks?${query.toString()}`);
  },

  async searchWeb(query, category = "all") {
    return this.request("/api/search/web", {
      method: "POST",
      body: JSON.stringify({ query, category }),
    });
  },

  // Snippets
  async getSnippets(language, q) {
    const query = new URLSearchParams();
    if (language) query.append("language", language);
    if (q) query.append("q", q);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return this.request(`/api/snippets${qs}`);
  },

  async createSnippet(data) {
    return this.request("/api/snippets", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async deleteSnippet(id) {
    return this.request(`/api/snippets/${id}`, {
      method: "DELETE",
    });
  },
};

window.API = API;
