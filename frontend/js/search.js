/**
 * DevSearch — Unified Developer Search Engine & Workspace
 * Multi-provider search across DevDocs, Stack Overflow, GitHub, Google,
 * Local Offline Documentation (SQLite FTS5), and Workspace Notebooks.
 * Features 1-click notebook insertion, result preview, history, bookmarks, and settings.
 */

class SearchWorkspace {
  constructor(panelEl, resizerEl, onInsertCallback) {
    this.panel = panelEl;
    this.resizer = resizerEl;
    this.onInsertCallback = onInsertCallback;

    this.currentView = "search"; // "search", "history", "saved", "docs", "settings"
    this.currentQuery = "";
    this.currentCategory = "all";
    this.currentLanguage = "";
    this.currentFramework = "";
    this.debounceTimer = null;
    this.isDragging = false;
    this.isExpanded = false;
    this.activePreviewItem = null;

    this.initDOM();
    this.attachEvents();
    this.performSearch(""); // Load initial suggested developer resources
  }

  initDOM() {
    this.panel.innerHTML = `
      <!-- DevSearch Header -->
      <div class="search-panel-header">
        <div class="search-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <span>DevSearch</span>
          <span class="devsearch-engine-badge">Unified Engine</span>
        </div>
        <div class="search-header-actions">
          <button type="button" class="btn btn-icon-sm btn-expand-search" title="Toggle Full Workspace / Split (50%)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>
          </button>
          <button type="button" class="btn btn-icon-sm btn-close-search" title="Close Search (Cmd+K)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
      </div>

      <!-- DevSearch Top Navigation Bar -->
      <div class="devsearch-nav-tabs">
        <button type="button" class="devsearch-nav-btn active" data-view="search">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          Search
        </button>
        <button type="button" class="devsearch-nav-btn" data-view="history">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          History
        </button>
        <button type="button" class="devsearch-nav-btn" data-view="saved">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>
          Saved
        </button>
        <button type="button" class="devsearch-nav-btn" data-view="docs">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
          Offline Docs
        </button>
        <button type="button" class="devsearch-nav-btn" data-view="settings">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
          Settings
        </button>
      </div>

      <!-- MAIN CONTAINER: Switches between Views -->
      <div class="devsearch-body-container">
        <!-- 1. SEARCH VIEW -->
        <div class="devsearch-view active" id="devsearch-view-search">
          <div class="search-input-wrapper">
            <svg class="search-icon-left" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            <input type="text" class="search-input-box" placeholder="Search docs, errors, code, GitHub, or Stack Overflow (Cmd+K)..." />
            <button type="button" class="search-clear-btn" title="Clear Search">✕</button>
          </div>

          <!-- Dynamic Category Tabs -->
          <div class="search-tabs-row">
            <button type="button" class="search-tab-pill active" data-category="all">All Sources</button>
            <button type="button" class="search-tab-pill" data-category="doc">Official Docs</button>
            <button type="button" class="search-tab-pill" data-category="code">Code Examples</button>
            <button type="button" class="search-tab-pill" data-category="stackoverflow">Stack Overflow</button>
            <button type="button" class="search-tab-pill" data-category="github">GitHub</button>
            <button type="button" class="search-tab-pill" data-category="offline">Offline (FTS5)</button>
            <button type="button" class="search-tab-pill" data-category="notebook">Notebooks</button>
          </div>

          <!-- Dynamic Filters: Language & Framework -->
          <div class="search-filters-bar">
            <select class="search-filter-select" id="search-filter-lang">
              <option value="">All Languages</option>
              <option value="python">Python</option>
              <option value="javascript">JavaScript / TypeScript</option>
              <option value="rust">Rust</option>
              <option value="go">Go</option>
              <option value="java">Java</option>
              <option value="c++">C / C++</option>
              <option value="sql">SQL / Postgres</option>
              <option value="dart">Dart / Flutter</option>
            </select>
            <select class="search-filter-select" id="search-filter-fw">
              <option value="">All Frameworks</option>
              <option value="fastapi">FastAPI</option>
              <option value="django">Django</option>
              <option value="react">React</option>
              <option value="node.js">Node.js</option>
              <option value="docker">Docker</option>
              <option value="git">Git</option>
              <option value="pytorch">PyTorch</option>
            </select>
          </div>

          <!-- Intent & Routing Status Banner -->
          <div class="search-intent-banner" style="display: none;"></div>

          <!-- Results List -->
          <div class="search-results-list">
            <div class="search-state-empty">
              <span>Loading developer resources...</span>
            </div>
          </div>
        </div>

        <!-- 2. HISTORY VIEW -->
        <div class="devsearch-view" id="devsearch-view-history">
          <div class="devsearch-section-header">
            <span>Recent Search History</span>
            <button type="button" class="btn btn-sm btn-clear-history" title="Clear all history">Clear All</button>
          </div>
          <div class="devsearch-history-list"></div>
        </div>

        <!-- 3. SAVED VIEW -->
        <div class="devsearch-view" id="devsearch-view-saved">
          <div class="devsearch-section-header">
            <span>Saved Bookmarks &amp; Resources</span>
            <span class="saved-count-badge">0 saved</span>
          </div>
          <div class="devsearch-saved-list"></div>
        </div>

        <!-- 4. OFFLINE DOCS VIEW -->
        <div class="devsearch-view" id="devsearch-view-docs">
          <div class="devsearch-section-header">
            <span>Local Offline Documentation (FTS5)</span>
          </div>
          <p class="devsearch-docs-desc">
            Download documentation indexes to search full-text without internet access. Powered by SQLite FTS5.
          </p>
          <div class="devsearch-doc-indexes-list"></div>
        </div>

        <!-- 5. SETTINGS VIEW -->
        <div class="devsearch-view" id="devsearch-view-settings">
          <div class="devsearch-section-header">
            <span>DevSearch Provider Configuration</span>
          </div>
          <form class="devsearch-settings-form">
            <div class="form-group">
              <label>Google Custom Search API Key</label>
              <input type="password" id="setting-google-key" class="form-input" placeholder="AIzaSy..." />
              <small class="form-hint">Enables inline Google web search results. Optional.</small>
            </div>
            <div class="form-group">
              <label>Google Search Engine ID (cx)</label>
              <input type="text" id="setting-google-cx" class="form-input" placeholder="017576662..." />
            </div>
            <div class="form-group">
              <label>GitHub Personal Access Token</label>
              <input type="password" id="setting-github-token" class="form-input" placeholder="ghp_..." />
              <small class="form-hint">Increases GitHub API rate limit from 60 to 5,000 req/hr. Optional.</small>
            </div>
            <div class="form-group">
              <label>Default Search Provider</label>
              <select id="setting-default-provider" class="form-input">
                <option value="all">Unified (All Providers)</option>
                <option value="devdocs">DevDocs / Official Docs</option>
                <option value="local_docs">Local Offline Docs</option>
                <option value="stackoverflow">Stack Overflow</option>
                <option value="github">GitHub</option>
                <option value="google">Google</option>
              </select>
            </div>
            <div class="form-group-checkbox">
              <label>
                <input type="checkbox" id="setting-enable-cache" checked />
                Enable In-Memory Response Caching
              </label>
            </div>
            <button type="button" class="btn btn-primary btn-save-settings">Save Settings</button>
          </form>
        </div>
      </div>

      <!-- Result Preview Drawer (Slide-in) -->
      <div class="devsearch-preview-drawer">
        <div class="preview-drawer-header">
          <span class="preview-source-badge">Preview</span>
          <button type="button" class="btn-close-preview" title="Close Preview">✕</button>
        </div>
        <div class="preview-drawer-content"></div>
        <div class="preview-drawer-actions">
          <button type="button" class="btn btn-primary btn-preview-insert-both">
            + Insert into Notebook
          </button>
          <a href="#" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-preview-open-link">
            Open Original Site ↗
          </a>
        </div>
      </div>
    `;

    // Cache DOM references
    this.searchInput = this.panel.querySelector(".search-input-box");
    this.clearBtn = this.panel.querySelector(".search-clear-btn");
    this.resultsList = this.panel.querySelector(".search-results-list");
    this.closeBtn = this.panel.querySelector(".btn-close-search");
    this.expandBtn = this.panel.querySelector(".btn-expand-search");
    this.categoryTabs = this.panel.querySelectorAll(".search-tab-pill");
    this.langFilter = this.panel.querySelector("#search-filter-lang");
    this.fwFilter = this.panel.querySelector("#search-filter-fw");
    this.intentBanner = this.panel.querySelector(".search-intent-banner");
    this.navBtns = this.panel.querySelectorAll(".devsearch-nav-btn");
    this.views = this.panel.querySelectorAll(".devsearch-view");
    this.previewDrawer = this.panel.querySelector(".devsearch-preview-drawer");
  }

  attachEvents() {
    // 1. Live Debounced Input
    this.searchInput.addEventListener("input", (e) => {
      this.currentQuery = e.target.value;
      this.clearBtn.classList.toggle("visible", !!this.currentQuery);

      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.performSearch(this.currentQuery);
      }, 250);
    });

    // Enter Key Search Immediate Trigger
    this.searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        clearTimeout(this.debounceTimer);
        this.performSearch(this.currentQuery);
      }
    });

    // 2. Clear Button
    this.clearBtn.addEventListener("click", () => {
      this.searchInput.value = "";
      this.currentQuery = "";
      this.clearBtn.classList.remove("visible");
      this.performSearch("");
      this.searchInput.focus();
    });

    // 3. Close & Expand Buttons
    this.closeBtn.addEventListener("click", () => this.toggleCollapse(true));
    this.expandBtn.addEventListener("click", () => this.toggleExpand());

    // 4. Category Tabs
    this.categoryTabs.forEach(tab => {
      tab.addEventListener("click", () => {
        this.categoryTabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        this.currentCategory = tab.dataset.category;
        this.performSearch(this.currentQuery);
      });
    });

    // 5. Language & Framework Filters
    this.langFilter.addEventListener("change", (e) => {
      this.currentLanguage = e.target.value;
      this.performSearch(this.currentQuery);
    });
    this.fwFilter.addEventListener("change", (e) => {
      this.currentFramework = e.target.value;
      this.performSearch(this.currentQuery);
    });

    // 6. Navigation Tabs (Search, History, Saved, Docs, Settings)
    this.navBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        this.navBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.switchView(btn.dataset.view);
      });
    });

    // 7. Preview Drawer Close
    const closePreviewBtn = this.previewDrawer.querySelector(".btn-close-preview");
    if (closePreviewBtn) {
      closePreviewBtn.addEventListener("click", () => this.closePreview());
    }

    // 8. Draggable Split Divider
    if (this.resizer) {
      this.initDraggableResizer();
    }
  }

  switchView(viewName) {
    this.currentView = viewName;
    this.views.forEach(v => v.classList.remove("active"));

    const target = this.panel.querySelector(`#devsearch-view-${viewName}`);
    if (target) target.classList.add("active");

    if (viewName === "history") this.loadHistory();
    else if (viewName === "saved") this.loadSavedResources();
    else if (viewName === "docs") this.loadDocIndexes();
    else if (viewName === "settings") this.loadSettings();
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
      const workspaceRect = document.getElementById("workspace-container").getBoundingClientRect();
      const newWidth = Math.max(340, Math.min(window.innerWidth * 0.75, e.clientX - workspaceRect.left));
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

  toggleExpand() {
    this.isExpanded = !this.isExpanded;
    if (this.isExpanded) {
      this.panel.style.width = "100%";
      this.panel.style.maxWidth = "100%";
      this.expandBtn.classList.add("active");
    } else {
      this.panel.style.width = "480px";
      this.panel.style.maxWidth = "60%";
      this.expandBtn.classList.remove("active");
    }
  }

  async performSearch(query) {
    try {
      this.resultsList.innerHTML = `
        <div class="search-state-empty">
          <div class="search-spinner"></div>
          <span>Searching unified developer sources...</span>
        </div>
      `;

      const payload = {
        query: query.trim(),
        category: this.currentCategory,
        language: this.currentLanguage || null,
        framework: this.currentFramework || null,
        limit: 25
      };

      const data = await API.unifiedSearch(payload);

      // Render Intent Banner if classified
      if (data.intent && query.trim()) {
        const intentText = data.intent === "error" ? "Error Troubleshooting" :
                           data.intent === "code" ? "Code Example Implementation" :
                           data.intent === "api" ? "API Reference" : "Documentation & Concepts";
        this.intentBanner.style.display = "flex";
        this.intentBanner.innerHTML = `
          <span>Query classified: <strong>${intentText}</strong></span>
          ${data.detected_language ? `<span class="badge badge-neutral">${data.detected_language}</span>` : ""}
          ${data.cached ? `<span class="badge badge-success" title="Instant cache response">Cached</span>` : ""}
        `;
      } else {
        this.intentBanner.style.display = "none";
      }

      this.renderResults(data.results || []);
    } catch (err) {
      this.resultsList.innerHTML = `
        <div class="search-state-empty" style="color: var(--error-text);">
          <span>Search failed: ${this.escapeHTML(err.message)}</span>
        </div>
      `;
    }
  }

  renderResults(results) {
    if (results.length === 0) {
      this.resultsList.innerHTML = `
        <div class="search-state-empty">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <span style="font-weight: 600; margin-top: 8px;">No results found for "${this.escapeHTML(this.currentQuery)}"</span>
          <span style="font-size: 12px; color: var(--text-subtle); margin-top: 4px;">Try searching another keyword or switching the source category tab.</span>
        </div>
      `;
      return;
    }

    this.resultsList.innerHTML = "";

    results.forEach(item => {
      const card = document.createElement("div");
      card.className = "search-result-card";

      // Badge style per category
      const cat = (item.category || "").toLowerCase();
      const catBadgeClass =
        cat === "stackoverflow" ? "badge-so" :
        cat === "github" ? "badge-gh" :
        cat === "offline" ? "badge-offline" :
        cat === "doc" ? "badge-doc" :
        cat === "error" ? "badge-warning" : "badge-neutral";

      const sourceLabel = item.source || cat.toUpperCase();

      card.innerHTML = `
        <div class="search-result-header">
          <div class="search-result-title">${this.escapeHTML(item.title)}</div>
          <span class="badge ${catBadgeClass}">${this.escapeHTML(cat)}</span>
        </div>
        <div class="search-result-snippet">${this.escapeHTML(item.snippet)}</div>
        ${item.code ? `
          <div class="search-result-code-container">
            <div class="code-box-header">
              <span>${this.escapeHTML(item.language || "code")}</span>
              <button type="button" class="btn-copy-code" title="Copy code">Copy</button>
            </div>
            <pre class="search-result-code"><code>${this.escapeHTML(item.code)}</code></pre>
          </div>
        ` : ""}
        <div class="search-result-meta-row">
          ${item.stars ? `<span>⭐ ${item.stars.toLocaleString()}</span>` : ""}
          ${item.score ? `<span>▲ ${item.score} votes</span>` : ""}
          ${item.is_answered ? `<span style="color: var(--success-text);">✓ Accepted</span>` : ""}
          ${item.date ? `<span>📅 ${this.escapeHTML(item.date)}</span>` : ""}
        </div>
        <div class="search-result-footer">
          <span class="search-result-source">${this.escapeHTML(sourceLabel)}</span>
          <div class="search-card-actions">
            <button type="button" class="btn-card-action btn-preview-action" title="Preview Result">👁 Preview</button>
            <button type="button" class="btn-card-action btn-insert-ref" title="Insert Reference into notebook">+ Ref</button>
            ${item.code ? `<button type="button" class="btn-card-action btn-insert-code" title="Insert Executable Code Block">+ Code</button>` : ""}
            <button type="button" class="btn-card-action btn-bookmark-action" title="Bookmark / Save Resource">🔖</button>
            ${item.url ? `<a href="${this.escapeHTML(item.url)}" target="_blank" rel="noopener noreferrer" class="btn-card-action" title="Open source link">↗</a>` : ""}
          </div>
        </div>
      `;

      // Copy Code
      const copyBtn = card.querySelector(".btn-copy-code");
      if (copyBtn && item.code) {
        copyBtn.addEventListener("click", () => {
          navigator.clipboard.writeText(item.code);
          copyBtn.textContent = "Copied!";
          setTimeout(() => (copyBtn.textContent = "Copy"), 1500);
        });
      }

      // Actions: Insert Ref & Insert Code
      const insertRefBtn = card.querySelector(".btn-insert-ref");
      insertRefBtn.addEventListener("click", () => {
        this.insertResultIntoNotebook(item, "reference");
      });

      const insertCodeBtn = card.querySelector(".btn-insert-code");
      if (insertCodeBtn) {
        insertCodeBtn.addEventListener("click", () => {
          this.insertResultIntoNotebook(item, "code");
        });
      }

      // Preview Action
      const previewBtn = card.querySelector(".btn-preview-action");
      previewBtn.addEventListener("click", () => {
        this.openPreview(item);
      });

      // Bookmark Action
      const bookmarkBtn = card.querySelector(".btn-bookmark-action");
      bookmarkBtn.addEventListener("click", async () => {
        try {
          await API.saveResource({
            title: item.title,
            snippet: item.snippet,
            code: item.code,
            language: item.language,
            source: item.source,
            url: item.url,
            category: item.category,
            folder: "General"
          });
          bookmarkBtn.textContent = "✓";
          bookmarkBtn.style.color = "var(--success-text)";
          setTimeout(() => (bookmarkBtn.textContent = "🔖"), 1500);
        } catch (_) {}
      });

      this.resultsList.appendChild(card);
    });
  }

  openPreview(item) {
    this.activePreviewItem = item;
    const content = this.previewDrawer.querySelector(".preview-drawer-content");
    const linkBtn = this.previewDrawer.querySelector(".btn-preview-open-link");
    const insertBtn = this.previewDrawer.querySelector(".btn-preview-insert-both");

    content.innerHTML = `
      <h3 style="font-size: 15px; font-weight: 700; margin-bottom: 8px; color: var(--text-primary);">${this.escapeHTML(item.title)}</h3>
      <div style="display: flex; gap: 6px; margin-bottom: 12px;">
        <span class="badge badge-neutral">${this.escapeHTML(item.source || item.category)}</span>
        ${item.language ? `<span class="badge badge-success">${this.escapeHTML(item.language)}</span>` : ""}
      </div>
      <div style="font-size: 13px; line-height: 1.6; color: var(--text-secondary); margin-bottom: 14px;">
        ${this.escapeHTML(item.snippet)}
      </div>
      ${item.code ? `
        <div style="font-weight: 600; font-size: 11.5px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 4px;">Code Snippet:</div>
        <pre class="search-result-code" style="max-height: 250px;"><code>${this.escapeHTML(item.code)}</code></pre>
      ` : ""}
    `;

    if (item.url) {
      linkBtn.href = item.url;
      linkBtn.style.display = "inline-flex";
    } else {
      linkBtn.style.display = "none";
    }

    insertBtn.onclick = () => {
      this.insertResultIntoNotebook(item, "both");
      this.closePreview();
    };

    this.previewDrawer.classList.add("open");
  }

  closePreview() {
    this.previewDrawer.classList.remove("open");
    this.activePreviewItem = null;
  }

  insertResultIntoNotebook(item, mode = "both") {
    if (typeof this.onInsertCallback === "function") {
      this.onInsertCallback(item, mode);
    }
  }

  // ------------------------------------------
  // History View
  // ------------------------------------------
  async loadHistory() {
    const list = this.panel.querySelector(".devsearch-history-list");
    list.innerHTML = `<div class="search-state-empty"><span>Loading search history...</span></div>`;

    try {
      const history = await API.getSearchHistory(30);
      if (history.length === 0) {
        list.innerHTML = `<div class="search-state-empty"><span>No search history recorded yet.</span></div>`;
        return;
      }

      list.innerHTML = "";
      history.forEach(h => {
        const row = document.createElement("div");
        row.className = "devsearch-history-row";
        row.innerHTML = `
          <div class="history-info">
            <span class="history-query">${this.escapeHTML(h.query)}</span>
            <span class="history-meta">${h.category} · ${h.results_count} results · ${h.created_at ? h.created_at.slice(0, 10) : ""}</span>
          </div>
          <div class="history-actions">
            <button type="button" class="btn-rerun-query" title="Run search again">🔍</button>
            <button type="button" class="btn-del-history" title="Delete entry">✕</button>
          </div>
        `;

        row.querySelector(".btn-rerun-query").addEventListener("click", () => {
          this.switchView("search");
          this.searchInput.value = h.query;
          this.currentQuery = h.query;
          this.performSearch(h.query);
        });

        row.querySelector(".btn-del-history").addEventListener("click", async () => {
          await API.deleteSearchHistory(h.id);
          row.remove();
        });

        list.appendChild(row);
      });

      // Clear all button
      const clearBtn = this.panel.querySelector(".btn-clear-history");
      clearBtn.onclick = async () => {
        await API.clearSearchHistory();
        list.innerHTML = `<div class="search-state-empty"><span>All search history cleared.</span></div>`;
      };
    } catch (err) {
      list.innerHTML = `<div class="search-state-empty" style="color: var(--error-text);">Failed to load history: ${this.escapeHTML(err.message)}</div>`;
    }
  }

  // ------------------------------------------
  // Saved Resources View
  // ------------------------------------------
  async loadSavedResources() {
    const list = this.panel.querySelector(".devsearch-saved-list");
    const countBadge = this.panel.querySelector(".saved-count-badge");
    list.innerHTML = `<div class="search-state-empty"><span>Loading bookmarks...</span></div>`;

    try {
      const saved = await API.getSavedResources();
      countBadge.textContent = `${saved.length} saved`;

      if (saved.length === 0) {
        list.innerHTML = `<div class="search-state-empty"><span>No bookmarked resources. Click 🔖 on any search result to save it here.</span></div>`;
        return;
      }

      list.innerHTML = "";
      saved.forEach(s => {
        const card = document.createElement("div");
        card.className = "search-result-card";
        card.innerHTML = `
          <div class="search-result-header">
            <div class="search-result-title">${this.escapeHTML(s.title)}</div>
            <span class="badge badge-neutral">${this.escapeHTML(s.folder || "General")}</span>
          </div>
          <div class="search-result-snippet">${this.escapeHTML(s.snippet)}</div>
          ${s.code ? `<pre class="search-result-code"><code>${this.escapeHTML(s.code)}</code></pre>` : ""}
          <div class="search-result-footer">
            <span class="search-result-source">${this.escapeHTML(s.source || "Saved")}</span>
            <div class="search-card-actions">
              <button type="button" class="btn-card-action btn-insert-saved" title="Insert into active notebook">+ Insert</button>
              <button type="button" class="btn-card-action btn-del-saved" title="Remove bookmark">✕</button>
            </div>
          </div>
        `;

        card.querySelector(".btn-insert-saved").addEventListener("click", () => {
          this.insertResultIntoNotebook(s, "both");
        });

        card.querySelector(".btn-del-saved").addEventListener("click", async () => {
          await API.deleteSavedResource(s.id);
          card.remove();
          this.loadSavedResources();
        });

        list.appendChild(card);
      });
    } catch (err) {
      list.innerHTML = `<div class="search-state-empty" style="color: var(--error-text);">Failed to load saved resources: ${this.escapeHTML(err.message)}</div>`;
    }
  }

  // ------------------------------------------
  // Offline Docs Manager View
  // ------------------------------------------
  async loadDocIndexes() {
    const list = this.panel.querySelector(".devsearch-doc-indexes-list");
    list.innerHTML = `<div class="search-state-empty"><span>Loading doc packs...</span></div>`;

    try {
      const indexes = await API.getDocIndexes();
      list.innerHTML = "";

      indexes.forEach(idx => {
        const row = document.createElement("div");
        row.className = "devsearch-doc-pack-row";
        const isDownloaded = idx.status === "downloaded";

        row.innerHTML = `
          <div class="doc-pack-info">
            <div class="doc-pack-title">${this.escapeHTML(idx.name)}</div>
            <div class="doc-pack-desc">${this.escapeHTML(idx.description || "")}</div>
            <div class="doc-pack-meta">
              <span class="badge ${isDownloaded ? 'badge-success' : 'badge-neutral'}">${isDownloaded ? '✓ Downloaded' : 'Available'}</span>
              <span>${idx.entry_count} entries</span>
              <span>v${idx.version}</span>
            </div>
          </div>
          <div class="doc-pack-actions">
            ${isDownloaded ? `
              <button type="button" class="btn btn-sm btn-reindex-doc" title="Re-index">Update</button>
              <button type="button" class="btn btn-sm btn-remove-doc" style="color: var(--error-text);" title="Remove">Remove</button>
            ` : `
              <button type="button" class="btn btn-sm btn-primary btn-download-doc">Download</button>
            `}
          </div>
        `;

        const dlBtn = row.querySelector(".btn-download-doc") || row.querySelector(".btn-reindex-doc");
        if (dlBtn) {
          dlBtn.addEventListener("click", async () => {
            dlBtn.textContent = "Indexing...";
            dlBtn.disabled = true;
            try {
              await API.downloadDocIndex(idx.id);
              this.loadDocIndexes();
            } catch (e) {
              alert(`Failed to index: ${e.message}`);
              dlBtn.disabled = false;
            }
          });
        }

        const rmBtn = row.querySelector(".btn-remove-doc");
        if (rmBtn) {
          rmBtn.addEventListener("click", async () => {
            if (confirm(`Remove ${idx.name} from local offline search?`)) {
              await API.deleteDocIndex(idx.id);
              this.loadDocIndexes();
            }
          });
        }

        list.appendChild(row);
      });
    } catch (err) {
      list.innerHTML = `<div class="search-state-empty" style="color: var(--error-text);">Failed to load doc indexes: ${this.escapeHTML(err.message)}</div>`;
    }
  }

  // ------------------------------------------
  // Settings View
  // ------------------------------------------
  async loadSettings() {
    try {
      const settings = await API.getSearchSettings();
      const googleCx = this.panel.querySelector("#setting-google-cx");
      const defaultProv = this.panel.querySelector("#setting-default-provider");
      const cacheCheckbox = this.panel.querySelector("#setting-enable-cache");

      if (settings.google_cse_id) googleCx.value = settings.google_cse_id;
      if (settings.default_provider) defaultProv.value = settings.default_provider;
      cacheCheckbox.checked = settings.enable_cache;

      const saveBtn = this.panel.querySelector(".btn-save-settings");
      saveBtn.onclick = async () => {
        saveBtn.textContent = "Saving...";
        const googleKey = this.panel.querySelector("#setting-google-key").value.trim();
        const ghToken = this.panel.querySelector("#setting-github-token").value.trim();

        const updateData = {
          default_provider: defaultProv.value,
          enable_cache: cacheCheckbox.checked
        };
        if (googleKey) updateData.google_api_key = googleKey;
        if (googleCx.value.trim()) updateData.google_cse_id = googleCx.value.trim();
        if (ghToken) updateData.github_token = ghToken;

        await API.updateSearchSettings(updateData);
        saveBtn.textContent = "Saved!";
        setTimeout(() => (saveBtn.textContent = "Save Settings"), 1500);
      };
    } catch (_) {}
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
