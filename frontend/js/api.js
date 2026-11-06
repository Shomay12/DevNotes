/**
 * DevNote API Client
 * Clean asynchronous HTTP interface to FastAPI backend
 * Supports token-based local network access & cross-edition configurations.
 */

const API = {
  // Retrieve token from query params or storage
  getAuthToken() {
    let paramToken = null;
    try {
      if (typeof window !== "undefined" && window.location && window.location.search) {
        const urlParams = new URLSearchParams(window.location.search);
        paramToken = urlParams.get("token");
      }
    } catch (_) {}
    if (paramToken) {
      try { localStorage.setItem("devnote_auth_token", paramToken); } catch (_) {}
      return paramToken;
    }
    try {
      return localStorage.getItem("devnote_auth_token") || "";
    } catch (_) {
      return "";
    }
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
      const contentType = (response.headers && typeof response.headers.get === "function") 
        ? response.headers.get("content-type") 
        : "";
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

  // Developer Search Workspace (DevSearch)
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

  async unifiedSearch(payload) {
    return this.request("/api/search", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getSearchProviders() {
    return this.request("/api/search/providers");
  },

  async getSearchHistory(limit = 20) {
    return this.request(`/api/search/history?limit=${limit}`);
  },

  async deleteSearchHistory(id) {
    return this.request(`/api/search/history/${id}`, {
      method: "DELETE",
    });
  },

  async clearSearchHistory() {
    return this.request("/api/search/history", {
      method: "DELETE",
    });
  },

  async searchOfflineDocs(query, indexId = null) {
    const params = new URLSearchParams({ q: query || "" });
    if (indexId) params.append("index_id", indexId);
    return this.request(`/api/search/docs?${params.toString()}`);
  },

  async getDocIndexes() {
    return this.request("/api/search/docs/indexes");
  },

  async downloadDocIndex(indexId) {
    return this.request("/api/search/docs/download", {
      method: "POST",
      body: JSON.stringify({ index_id: indexId }),
    });
  },

  async deleteDocIndex(indexId) {
    return this.request(`/api/search/docs/indexes/${indexId}`, {
      method: "DELETE",
    });
  },

  async getSavedResources(folder = null) {
    const params = new URLSearchParams();
    if (folder) params.append("folder", folder);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return this.request(`/api/search/saved${qs}`);
  },

  async saveResource(data) {
    return this.request("/api/search/saved", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async deleteSavedResource(id) {
    return this.request(`/api/search/saved/${id}`, {
      method: "DELETE",
    });
  },

  async getBookmarks(folder = null) {
    const params = new URLSearchParams();
    if (folder) params.append("folder", folder);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return this.request(`/api/search/bookmarks${qs}`);
  },

  async saveBookmark(data) {
    return this.request("/api/search/bookmarks", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async deleteBookmark(id) {
    return this.request(`/api/search/bookmarks/${id}`, {
      method: "DELETE",
    });
  },

  async getSearchSettings() {
    return this.request("/api/search/settings");
  },

  async updateSearchSettings(data) {
    return this.request("/api/search/settings", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  // Research Reader
  async readResearchContent(url, refresh = false) {
    const params = new URLSearchParams({ url, refresh: refresh ? "true" : "false" });
    return this.request(`/api/research/read?${params.toString()}`);
  },

  async checkIframeFraming(url) {
    const params = new URLSearchParams({ url });
    return this.request(`/api/research/check-frame?${params.toString()}`);
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

  // Hacker News Tech Feed
  async getHackerNews(feed = "top", limit = 25, query = "") {
    const params = new URLSearchParams({ feed, limit: String(limit) });
    if (query) params.append("query", query);
    return this.request(`/api/news/hackernews?${params.toString()}`);
  },

  // LLM & AI Assistant Add-On
  async chatWithLLM(data) {
    return this.request("/api/llm/chat", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async testLLMConnection(data) {
    return this.request("/api/llm/test", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getLLMConfig() {
    return this.request("/api/llm/config");
  },
};

window.API = API;
