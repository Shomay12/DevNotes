/**
 * DevNote — Developer Search Workspace
 * Real-time searching of concepts, errors, docs, code snippets,
 * notebooks, and web resources with 1-click notebook insertion.
 */

class SearchWorkspace {
  constructor(panelEl, resizerEl, onInsertCallback) {
    this.panel = panelEl;
    this.resizer = resizerEl;
    this.onInsertCallback = onInsertCallback;

    this.currentQuery = "";
    this.currentCategory = "all";
    this.debounceTimer = null;
    this.isDragging = false;

    this.initDOM();
    this.attachEvents();
    this.performSearch(""); // Load initial suggested concepts
  }

  initDOM() {
    this.panel.innerHTML = `
      <div class="search-panel-header">
        <div class="search-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          Developer Search Workspace
        </div>
        <div style="display: flex; align-items: center; gap: 4px;">
          <button type="button" class="btn btn-icon-sm btn-close-search" title="Close Search (Cmd+K)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
      </div>
      <div class="search-input-wrapper">
        <svg class="search-icon-left" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <input type="text" class="search-input-box" placeholder="Search concepts, errors, docs, code, or web (Cmd+K)..." />
        <button type="button" class="search-clear-btn" title="Clear Search">✕</button>
      </div>
      <div class="search-tabs-row">
        <button type="button" class="search-tab-pill active" data-category="all">All</button>
        <button type="button" class="search-tab-pill" data-category="concept">Concepts</button>
        <button type="button" class="search-tab-pill" data-category="error">Error Fixes</button>
        <button type="button" class="search-tab-pill" data-category="code">Code</button>
        <button type="button" class="search-tab-pill" data-category="doc">Docs</button>
        <button type="button" class="search-tab-pill" data-category="notebook">Notebooks</button>
      </div>
      <div class="search-results-list">
        <div class="search-state-empty">
          <span>Loading developer resources...</span>
        </div>
      </div>
    `;

    this.searchInput = this.panel.querySelector(".search-input-box");
    this.clearBtn = this.panel.querySelector(".search-clear-btn");
    this.resultsList = this.panel.querySelector(".search-results-list");
    this.closeBtn = this.panel.querySelector(".btn-close-search");
    this.categoryTabs = this.panel.querySelectorAll(".search-tab-pill");
  }

  attachEvents() {
    // Live Debounced Input
    this.searchInput.addEventListener("input", (e) => {
      this.currentQuery = e.target.value;
      this.clearBtn.classList.toggle("visible", !!this.currentQuery);

      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.performSearch(this.currentQuery);
      }, 200);
    });

    // Clear Button
    this.clearBtn.addEventListener("click", () => {
      this.searchInput.value = "";
      this.currentQuery = "";
      this.clearBtn.classList.remove("visible");
      this.performSearch("");
      this.searchInput.focus();
    });

    // Close Button
    this.closeBtn.addEventListener("click", () => {
      this.toggleCollapse(true);
    });

    // Category Tabs
    this.categoryTabs.forEach(tab => {
      tab.addEventListener("click", () => {
        this.categoryTabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        this.currentCategory = tab.dataset.category;
        this.performSearch(this.currentQuery);
      });
    });

    // Draggable Split Divider
    if (this.resizer) {
      this.initDraggableResizer();
    }
  }

  initDraggableResizer() {
    const onMouseDown = (e) => {
      e.preventDefault();
      this.isDragging = true;
      this.resizer.classList.add("dragging");
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";

      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("mouseup", onMouseUp);
    };

    const onMouseMove = (e) => {
      if (!this.isDragging) return;
      // Calculate panel width from the left edge of workspace container
      const workspaceRect = document.getElementById("workspace-container").getBoundingClientRect();
      const newWidth = Math.max(300, Math.min(window.innerWidth * 0.7, e.clientX - workspaceRect.left));
      this.panel.style.width = `${newWidth}px`;
    };

    const onMouseUp = () => {
      if (this.isDragging) {
        this.isDragging = false;
        this.resizer.classList.remove("dragging");
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
      }
    };

    this.resizer.addEventListener("mousedown", onMouseDown);
  }

  async performSearch(query) {
    try {
      this.resultsList.innerHTML = `
        <div class="search-state-empty">
          <span>Searching documentation & notebooks...</span>
        </div>
      `;

      const data = await API.searchNotebooks(query, this.currentCategory);
      this.renderResults(data.results || []);
    } catch (err) {
      this.resultsList.innerHTML = `
        <div class="search-state-empty" style="color: var(--error-text);">
          <span>Search failed: ${err.message}</span>
        </div>
      `;
    }
  }

  renderResults(results) {
    if (results.length === 0) {
      this.resultsList.innerHTML = `
        <div class="search-state-empty">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <span style="font-weight: 500;">No results found for "${this.currentQuery}"</span>
          <span style="font-size: 12px; color: var(--text-subtle);">Try checking spelling or switching category</span>
        </div>
      `;
      return;
    }

    this.resultsList.innerHTML = "";

    results.forEach(item => {
      const card = document.createElement("div");
      card.className = "search-result-card";

      const catBadgeClass =
        item.category === "concept" ? "badge-neutral" :
        item.category === "error" ? "badge-warning" :
        item.category === "code" ? "badge-success" :
        item.category === "notebook" ? "badge-neutral" : "badge-neutral";

      const sourceLabel = item.source || item.category.toUpperCase();

      card.innerHTML = `
        <div class="search-result-header">
          <div class="search-result-title">${this.escapeHTML(item.title)}</div>
          <span class="badge ${catBadgeClass}">${item.category}</span>
        </div>
        <div class="search-result-snippet">${this.escapeHTML(item.snippet)}</div>
        ${item.code ? `<div class="search-result-code">${this.escapeHTML(item.code)}</div>` : ""}
        <div class="search-result-footer">
          <span class="search-result-source">${this.escapeHTML(sourceLabel)}</span>
          <button type="button" class="btn-insert-notebook" title="Insert directly into current notebook">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14"></path><path d="M5 12h14"></path></svg>
            Insert into Notebook
          </button>
        </div>
      `;

      const insertBtn = card.querySelector(".btn-insert-notebook");
      insertBtn.addEventListener("click", () => {
        this.insertResultIntoNotebook(item);
      });

      this.resultsList.appendChild(card);
    });
  }

  insertResultIntoNotebook(item) {
    if (typeof this.onInsertCallback === "function") {
      this.onInsertCallback(item);
    }
  }

  toggleCollapse(forceCollapse = null) {
    const isCurrentlyCollapsed = this.panel.classList.contains("collapsed");
    const shouldCollapse = forceCollapse !== null ? forceCollapse : !isCurrentlyCollapsed;

    this.panel.classList.toggle("collapsed", shouldCollapse);
    if (this.resizer) {
      this.resizer.style.display = shouldCollapse ? "none" : "block";
    }

    if (!shouldCollapse) {
      setTimeout(() => this.searchInput.focus(), 50);
    }
  }

  isOpen() {
    return !this.panel.classList.contains("collapsed");
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

window.SearchWorkspace = SearchWorkspace;
