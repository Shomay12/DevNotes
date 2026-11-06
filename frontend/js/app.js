/**
 * DevNote — Main Application Controller
 * Coordinates Sidebar Navigation, Editor Workspace, Developer Search,
 * Modals, Snippet Library, and Theme Management.
 */

class DevNoteApp {
  constructor() {
    this.currentNotebook = null;
    this.notebooks = [];
    this.activeNav = "notebooks";
    this.appConfig = { edition: "local", version: "1.1.0" };

    this.initTheme();
    this.initDOM();
    this.initSidebarState();
    this.initSubsystems();
    this.attachEvents();
    this.loadAppConfig();
    this.loadNotebookList();
  }

  async loadAppConfig() {
    try {
      this.appConfig = await API.getConfig();
      const badge = document.querySelector(".brand-badge");
      if (badge) {
        badge.textContent = this.appConfig.edition === "hosted" ? "HOSTED" : "LOCAL";
        badge.title = this.appConfig.edition === "hosted"
          ? "DevNote Hosted iPad Edition"
          : "DevNote Local Developer Edition (100% Free & Private)";
      }

      // Monetization & Sponsorship: Only display in Hosted Edition
      const sponsorSlot = document.getElementById("hosted-sponsor-slot");
      if (sponsorSlot) {
        if (this.appConfig.edition === "hosted") {
          sponsorSlot.style.display = "block";
        } else {
          // Strictly hidden in Local Developer Edition
          sponsorSlot.style.display = "none";
        }
      }
    } catch (_) {}
  }

  initTheme() {
    const savedTheme = localStorage.getItem("devnote_theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
  }

  toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    const next = current === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("devnote_theme", next);

    const btn = document.querySelector(".theme-toggle-btn span");
    if (btn) btn.textContent = next === "dark" ? "Light Mode" : "Dark Mode";
  }

  initDOM() {
    this.sidebar = document.getElementById("app-sidebar");
    this.btnSidebarCollapse = document.getElementById("btn-sidebar-collapse");
    this.notebookListContainer = document.getElementById("sidebar-notebook-list");
    this.btnNewNotebook = document.getElementById("btn-new-notebook");
    this.toastContainer = document.getElementById("toast-container");
    this.snippetsModal = document.getElementById("snippets-modal");

    // Set initial toggle label
    const theme = document.documentElement.getAttribute("data-theme");
    const toggleLabel = document.querySelector(".theme-toggle-btn span");
    if (toggleLabel) {
      toggleLabel.textContent = theme === "dark" ? "Light Mode" : "Dark Mode";
    }
  }

  initSidebarState() {
    const isCollapsed = localStorage.getItem("devnote_sidebar_collapsed") === "true";
    if (isCollapsed && this.sidebar) {
      this.sidebar.classList.add("collapsed");
    }
  }

  toggleSidebar(forceState) {
    if (!this.sidebar) return;
    const isMobile = window.innerWidth <= 768;
    if (isMobile) {
      const isOpen = this.sidebar.classList.contains("mobile-open");
      const shouldOpen = forceState !== undefined ? !forceState : !isOpen;
      this.sidebar.classList.toggle("mobile-open", shouldOpen);
    } else {
      const isCurrentlyCollapsed = this.sidebar.classList.contains("collapsed");
      const shouldCollapse = forceState !== undefined ? forceState : !isCurrentlyCollapsed;
      this.sidebar.classList.toggle("collapsed", shouldCollapse);
      localStorage.setItem("devnote_sidebar_collapsed", shouldCollapse ? "true" : "false");
    }
  }

  initSubsystems() {
    // 1. Initialize Document Editor
    const editorContainer = document.getElementById("notebook-workspace");
    this.editor = new NotebookEditor(editorContainer, this);

    // 2. Initialize Developer Search Workspace
    const searchPanel = document.getElementById("developer-search-panel");
    const resizer = document.getElementById("split-resizer");
    this.searchWorkspace = new SearchWorkspace(searchPanel, resizer, (searchItem, mode) => {
      this.editor.insertSearchResult(searchItem, mode);
    });

    // 3. Initialize PDF Manager
    this.pdfManager = new PDFManager(this);
  }

  attachEvents() {
    // Sidebar Collapse Button inside sidebar header
    if (this.btnSidebarCollapse) {
      this.btnSidebarCollapse.addEventListener("click", () => this.toggleSidebar());
    }

    // Global keyboard shortcut: Cmd+B / Ctrl+B or Cmd+\
    window.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && (e.key === "b" || e.key === "B" || e.key === "\\")) {
        e.preventDefault();
        this.toggleSidebar();
      }
    });

    // Close mobile drawer on outside tap
    document.addEventListener("click", (e) => {
      if (window.innerWidth <= 768 && this.sidebar && this.sidebar.classList.contains("mobile-open")) {
        if (!this.sidebar.contains(e.target) && !e.target.closest("#btn-sidebar-toggle")) {
          this.sidebar.classList.remove("mobile-open");
        }
      }
    });

    // New Notebook Button
    this.btnNewNotebook.addEventListener("click", () => this.handleCreateNotebook());

    // Theme Toggle Button
    const themeBtn = document.querySelector(".theme-toggle-btn");
    if (themeBtn) {
      themeBtn.addEventListener("click", () => this.toggleTheme());
    }

    // Navigation Menu items
    const navItems = document.querySelectorAll(".sidebar-nav .nav-item");
    navItems.forEach(item => {
      item.addEventListener("click", () => {
        navItems.forEach(i => i.classList.remove("active"));
        item.classList.add("active");
        const nav = item.dataset.nav;
        this.handleNavSwitch(nav);
      });
    });

    // Snippets Modal Controls
    if (this.snippetsModal) {
      this.snippetsModal.querySelectorAll(".btn-close-modal").forEach(b => {
        b.addEventListener("click", () => this.closeSnippetsModal());
      });

      const btnCreateSnippet = this.snippetsModal.querySelector(".btn-create-snippet");
      if (btnCreateSnippet) {
        btnCreateSnippet.addEventListener("click", () => this.handleCreateSnippet());
      }
    }

    // Network Auth Modal Controls
    this.authModal = document.getElementById("auth-modal");
    if (this.authModal) {
      const btnSaveToken = this.authModal.querySelector(".btn-save-token");
      if (btnSaveToken) {
        btnSaveToken.addEventListener("click", () => {
          const input = this.authModal.querySelector("#auth-token-input");
          if (input && input.value.trim()) {
            API.setAuthToken(input.value.trim());
            this.authModal.classList.remove("open");
            this.showToast("Access token applied!", "success");
            this.loadNotebookList();
          }
        });
      }
    }

    // Listen for 401 unauthorized over LAN
    window.addEventListener("devnote:auth_required", () => {
      if (this.authModal) {
        this.authModal.classList.add("open");
      }
    });
  }

  async exportCurrentNotebookJSON() {
    if (!this.currentNotebook) {
      this.showToast("No notebook is open to export.", "error");
      return;
    }
    try {
      await this.editor.saveNow();
      const res = await API.exportJSON(this.currentNotebook.id);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${this.currentNotebook.title.replace(/[^a-zA-Z0-9_\-]/g, "_")}_${this.currentNotebook.id.slice(0, 8)}.devnote.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      this.showToast("Exported JSON notebook!", "success");
    } catch (err) {
      this.showToast(`JSON export failed: ${err.message}`, "error");
    }
  }

  async handleNavSwitch(nav) {
    this.activeNav = nav;

    if (nav === "search") {
      this.searchWorkspace.toggleCollapse(false);
      this.searchWorkspace.switchView("search");
    } else if (nav === "llm") {
      this.searchWorkspace.toggleCollapse(false);
      this.searchWorkspace.switchView("llm");
    } else if (nav === "snippets") {
      this.openSnippetsModal();
    } else if (nav === "recent") {
      const recent = await API.getRecentNotebooks(10);
      this.renderSidebarNotebooks(recent);
    } else if (nav === "archived") {
      const archived = await API.getNotebooks({ archived: true });
      this.renderSidebarNotebooks(archived);
    } else {
      // Home / My Notebooks
      this.loadNotebookList();
    }
  }

  async loadNotebookList() {
    try {
      this.notebooks = await API.getNotebooks({ archived: false });
      this.renderSidebarNotebooks(this.notebooks);

      // If no notebook is active and notebooks exist, open the first one
      if (!this.currentNotebook && this.notebooks.length > 0) {
        const lastOpenedId = localStorage.getItem("devnote_last_notebook_id");
        const match = this.notebooks.find(n => n.id === lastOpenedId);
        const targetId = match ? match.id : this.notebooks[0].id;
        await this.openNotebook(targetId);
      }
    } catch (err) {
      console.error("Failed to load notebooks:", err);
    }
  }

  renderSidebarNotebooks(list) {
    this.notebookListContainer.innerHTML = "";

    if (list.length === 0) {
      this.notebookListContainer.innerHTML = `
        <div style="padding: 20px 10px; text-align: center; color: var(--text-muted); font-size: 12px;">
          No notebooks found.<br>Click "+ New Notebook" to start!
        </div>
      `;
      return;
    }

    list.forEach(nb => {
      const card = document.createElement("div");
      card.className = "notebook-card";
      card.dataset.notebookId = nb.id;

      if (this.currentNotebook && this.currentNotebook.id === nb.id) {
        card.classList.add("active");
      }

      const dateStr = nb.last_edited_at
        ? new Date(nb.last_edited_at).toLocaleDateString([], { month: "short", day: "numeric" })
        : "";

      const tagsHtml = (nb.tags || [])
        .slice(0, 3)
        .map(t => `<span class="notebook-tag-pill">#${this.escapeHTML(t)}</span>`)
        .join("");

      const pdfBadge = nb.pdf_export_path
        ? `<span class="notebook-pdf-badge">PDF</span>`
        : "";

      card.innerHTML = `
        <div class="notebook-card-header">
          <div class="notebook-card-title">${this.escapeHTML(nb.title)}</div>
          ${pdfBadge}
        </div>
        <div class="notebook-card-meta">
          <span>${nb.block_count || (nb.blocks ? nb.blocks.length : 0)} blocks</span>
          <span>${dateStr}</span>
        </div>
        ${tagsHtml ? `<div class="notebook-tags-row">${tagsHtml}</div>` : ""}
      `;

      card.addEventListener("click", () => {
        this.openNotebook(nb.id);
      });

      this.notebookListContainer.appendChild(card);
    });
  }

  async openNotebook(notebookId) {
    try {
      // Save current notebook before switching
      if (this.editor && this.editor.hasUnsavedChanges) {
        await this.editor.saveNow();
      }

      const fullNotebook = await API.getNotebook(notebookId);
      this.currentNotebook = fullNotebook;
      localStorage.setItem("devnote_last_notebook_id", notebookId);

      // Update sidebar active highlights
      const cards = this.notebookListContainer.querySelectorAll(".notebook-card");
      cards.forEach(c => {
        c.classList.toggle("active", c.dataset.notebookId === notebookId);
      });

      // Load into editor
      this.editor.loadNotebook(fullNotebook);
    } catch (err) {
      this.showToast(`Failed to open notebook: ${err.message}`, "error");
    }
  }

  async handleCreateNotebook() {
    try {
      const newNb = await API.createNotebook({
        title: "Untitled Notebook",
        tags: ["dev"],
      });

      this.showToast("Created new notebook", "success");
      await this.loadNotebookList();
      await this.openNotebook(newNb.id);
    } catch (err) {
      this.showToast(`Failed to create notebook: ${err.message}`, "error");
    }
  }

  updateSidebarNotebookTitle(notebookId, newTitle) {
    const card = this.notebookListContainer.querySelector(`[data-notebook-id="${notebookId}"]`);
    if (card) {
      const titleEl = card.querySelector(".notebook-card-title");
      if (titleEl) titleEl.textContent = newTitle || "Untitled Notebook";
    }
  }

  // Snippets Library Modal
  async openSnippetsModal() {
    this.snippetsModal.classList.add("open");
    await this.loadSnippetsList();
  }

  closeSnippetsModal() {
    this.snippetsModal.classList.remove("open");
  }

  async loadSnippetsList() {
    const container = this.snippetsModal.querySelector(".snippets-list-container");
    container.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--text-muted);">Loading snippets...</div>`;

    try {
      const snippets = await API.getSnippets();
      if (snippets.length === 0) {
        container.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--text-muted);">No snippets saved yet. Add your first snippet below!</div>`;
        return;
      }

      container.innerHTML = "";
      snippets.forEach(s => {
        const item = document.createElement("div");
        item.className = "search-result-card";
        item.style.marginBottom = "10px";

        item.innerHTML = `
          <div class="search-result-header">
            <div class="search-result-title">${this.escapeHTML(s.title)}</div>
            <span class="badge badge-neutral">${s.language.toUpperCase()}</span>
          </div>
          ${s.description ? `<div class="search-result-snippet">${this.escapeHTML(s.description)}</div>` : ""}
          <div class="search-result-code">${this.escapeHTML(s.code)}</div>
          <div class="search-result-footer">
            <button type="button" class="btn btn-sm btn-insert-snippet" style="background-color: var(--accent-light); color: var(--accent-primary);">
              Insert into Notebook
            </button>
            <button type="button" class="btn btn-sm btn-delete-snippet" style="color: var(--error-text);">
              Delete
            </button>
          </div>
        `;

        item.querySelector(".btn-insert-snippet").addEventListener("click", () => {
          this.editor.insertSearchResult({
            title: s.title,
            snippet: s.description,
            code: s.code,
            language: s.language,
          });
          this.closeSnippetsModal();
        });

        item.querySelector(".btn-delete-snippet").addEventListener("click", async () => {
          if (confirm(`Delete snippet '${s.title}'?`)) {
            await API.deleteSnippet(s.id);
            this.loadSnippetsList();
          }
        });

        container.appendChild(item);
      });
    } catch (err) {
      container.innerHTML = `<div style="color: var(--error-text); padding: 10px;">Failed to load snippets: ${err.message}</div>`;
    }
  }

  async handleCreateSnippet() {
    const titleInput = this.snippetsModal.querySelector("#new-snippet-title");
    const langSelect = this.snippetsModal.querySelector("#new-snippet-lang");
    const codeInput = this.snippetsModal.querySelector("#new-snippet-code");
    const descInput = this.snippetsModal.querySelector("#new-snippet-desc");

    if (!titleInput.value.trim() || !codeInput.value.trim()) {
      this.showToast("Title and code are required", "error");
      return;
    }

    try {
      await API.createSnippet({
        title: titleInput.value.trim(),
        language: langSelect.value,
        code: codeInput.value,
        description: descInput.value.trim(),
      });

      titleInput.value = "";
      codeInput.value = "";
      descInput.value = "";

      this.showToast("Snippet saved!", "success");
      await this.loadSnippetsList();
    } catch (err) {
      this.showToast(`Failed to save snippet: ${err.message}`, "error");
    }
  }

  // Toast Notification System
  showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span>${this.escapeHTML(message)}</span>
    `;

    this.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 300);
    }, 3200);
  }

  escapeHTML(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
}

// Bootstrap Application on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  window.app = new DevNoteApp();
});
