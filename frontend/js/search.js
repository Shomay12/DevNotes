/**
 * DevSearch Lite — Side-by-Side Developer Research Workspace
 * Multi-provider search across SearXNG, DevDocs, Stack Overflow, GitHub,
 * Google, Local Offline Documentation (SQLite FTS5), and Workspace Notebooks.
 * Features an integrated sandboxed Research Reader, study & evidence capture,
 * resizable split workspace, and offline resilience.
 */

class SearchWorkspace {
  constructor(panelEl, resizerEl, onInsertCallback) {
    this.panel = panelEl;
    this.resizer = resizerEl;
    this.onInsertCallback = onInsertCallback;

    this.currentView = "search"; // "search", "browser", "history", "saved", "docs", "settings"
    this.currentQuery = "";
    this.currentCategory = "all";
    this.currentLanguage = "";
    this.currentFramework = "";
    this.debounceTimer = null;
    this.isDragging = false;
    this.isExpanded = false;
    this.activePreviewItem = null;
    this.currentBrowserItem = null;
    this.activeAbortController = null;

    // Research Reader state
    this.readerHistory = [];
    this.readerHistoryIndex = -1;
    this.readerFontSize = 14;
    this.readerWidth = "standard"; // "standard", "wide", "full"
    this.readerSearchMatches = [];
    this.currentMatchIndex = -1;
    this.selectedText = "";

    this.initDOM();
    this.attachEvents();
    this.restoreSavedLayout();
    this.updateOnlineStatus();

    // Load initial suggested developer resources
    this.performSearch("");
  }

  initDOM() {
    this.panel.innerHTML = `
      <!-- DevSearch Header -->
      <div class="search-panel-header">
        <div class="search-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <span>Search</span>
        </div>
        <div class="search-header-actions">
          <button type="button" class="btn btn-icon-sm btn-split-search" title="Reset to Split View (50% / 50%)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="12" y1="3" x2="12" y2="21"></line></svg>
          </button>
          <button type="button" class="btn btn-icon-sm btn-expand-search" title="Toggle Full Workspace / Split">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>
          </button>
          <button type="button" class="btn btn-sm btn-close-search" title="Close Search (Esc or Cmd+K)">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            Close
          </button>
        </div>
      </div>

      <!-- DevSearch Top Navigation Bar -->
      <div class="devsearch-nav-tabs">
        <button type="button" class="devsearch-nav-btn active" data-view="search">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          Search
        </button>
        <button type="button" class="devsearch-nav-btn" data-view="browser">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>
          Reader
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
        <button type="button" class="devsearch-nav-btn" data-view="llm">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2z"></path><path d="M12 8v4"></path><path d="M12 16h.01"></path></svg>
          Assistant
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
          <div class="devsearch-offline-banner" style="display: none;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="1" y1="1" x2="23" y2="23"></line><path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"></path><path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"></path><path d="M10.71 5.05A16 16 0 0 1 22.58 9"></path><path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"></path><path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path><line x1="12" y1="20" x2="12.01" y2="20"></line></svg>
            <span>Offline Mode</span>
          </div>

          <div class="search-input-wrapper">
            <svg class="search-icon-left" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            <input type="text" class="search-input-box" placeholder="Search documentation, Wikipedia, Hacker News, Stack Overflow..." />
            <button type="button" class="search-clear-btn" title="Clear Search">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>

          <!-- Dynamic Category Tabs -->
          <div class="search-tabs-row">
            <button type="button" class="search-tab-pill active" data-category="all">All Sources</button>
            <button type="button" class="search-tab-pill" data-category="general">General Web</button>
            <button type="button" class="search-tab-pill" data-category="doc">Official Docs</button>
            <button type="button" class="search-tab-pill" data-category="stackoverflow">Stack Overflow</button>
            <button type="button" class="search-tab-pill" data-category="github">GitHub</button>
          </div>

          <!-- Results List -->
          <div class="search-results-list">
            <div class="search-state-empty">
              <span>Loading developer resources...</span>
            </div>
          </div>
        </div>

        <!-- 2. INTEGRATED RESEARCH READER VIEW -->
        <div class="devsearch-view" id="devsearch-view-browser">
          <!-- Reader Navigation Toolbar -->
          <div class="research-browser-toolbar">
            <button type="button" class="btn-browser-back-results" title="Back to Search Results">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"></polyline></svg>
              <span>Results</span>
            </button>
            <button type="button" class="btn btn-icon-sm btn-browser-nav-back" title="History Back (Alt+Left)" disabled>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
            </button>
            <button type="button" class="btn btn-icon-sm btn-browser-nav-forward" title="History Forward (Alt+Right)" disabled>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
            </button>
            <button type="button" class="btn btn-icon-sm btn-browser-nav-reload" title="Reload &amp; Re-extract Source">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
            </button>

            <div class="browser-url-bar-wrapper">
              <input type="text" class="browser-url-input" placeholder="Enter webpage URL (https://...) or raw search query..." />
              <span class="reader-strategy-pill doc" id="reader-strategy-pill" title="Current Reading Strategy">Native Reader</span>
            </div>

            <!-- Font Size Controls -->
            <button type="button" class="btn btn-icon-sm btn-reader-font-down" title="Decrease Font Size (A-)">
              <span style="font-size: 11px; font-weight: 700;">A-</span>
            </button>
            <button type="button" class="btn btn-icon-sm btn-reader-font-up" title="Increase Font Size (A+)">
              <span style="font-size: 13px; font-weight: 700;">A+</span>
            </button>

            <!-- Reading Width Toggle -->
            <button type="button" class="btn btn-icon-sm btn-reader-width-toggle" title="Toggle Reading Width (Standard / Wide / Full)">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"></rect><line x1="7" y1="4" x2="7" y2="20"></line><line x1="17" y1="4" x2="17" y2="20"></line></svg>
            </button>

            <!-- In-page Search Toggle -->
            <button type="button" class="btn btn-icon-sm btn-reader-find-toggle" title="Find in Article (Cmd+F / Ctrl+F)">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            </button>

            <!-- Copy Citation -->
            <button type="button" class="btn btn-icon-sm btn-reader-copy-citation" title="Copy Formatted Citation">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
            </button>

            <button type="button" class="btn btn-icon-sm btn-browser-copy-url" title="Copy URL">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            </button>
            <button type="button" class="btn btn-icon-sm btn-browser-bookmark" title="Bookmark / Save Resource">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>
            </button>
            <a href="#" target="_blank" rel="noopener noreferrer" class="btn btn-icon-sm btn-browser-open-external" title="Open in Original Browser Tab ↗">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>
          </div>

          <!-- Reader In-Page Find Bar -->
          <div class="reader-find-bar" id="reader-find-bar">
            <input type="text" class="reader-find-input" placeholder="Find in article..." />
            <span class="reader-find-count">0 / 0</span>
            <button type="button" class="btn btn-icon-sm btn-find-prev" title="Previous match">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"></polyline></svg>
            </button>
            <button type="button" class="btn btn-icon-sm btn-find-next" title="Next match">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </button>
            <button type="button" class="btn btn-icon-sm btn-find-close" title="Close find bar">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>

          <!-- Reader Content Frame & Fallback Container -->
          <div class="research-browser-frame-container" id="reader-frame-container">
            <!-- 1. Native Extracted Reader View -->
            <div class="research-reader-wrapper width-standard" id="reader-native-view">
              <div class="reader-article-content">
                <div class="reader-article-header" id="reader-article-header">
                  <h1 class="reader-article-title" id="reader-article-title">Select a resource to read</h1>
                  <div class="reader-article-meta" id="reader-article-meta"></div>
                </div>
                <div class="reader-article-body" id="reader-article-body"></div>
              </div>
            </div>

            <!-- 2. Loading Skeleton View -->
            <div class="reader-skeleton" id="reader-loading-view" style="display: none;">
              <div class="skeleton-bar skeleton-title"></div>
              <div class="skeleton-bar skeleton-meta"></div>
              <div class="skeleton-bar skeleton-card"></div>
              <div class="skeleton-bar skeleton-text"></div>
              <div class="skeleton-bar skeleton-text-short"></div>
              <div class="skeleton-bar skeleton-code"></div>
              <div class="skeleton-bar skeleton-text"></div>
            </div>

            <!-- 3. Polished Fallback View (Restricted / External Only) -->
            <div class="reader-fallback-view" id="reader-fallback-view" style="display: none;">
              <div class="reader-fallback-banner restricted">
                <div class="reader-fallback-info">
                  <div class="reader-fallback-title" id="fallback-status-title">External Technical Resource</div>
                  <div class="reader-fallback-desc" id="fallback-status-desc">
                    This resource restricts automated in-app reading. You can open the official documentation directly in a new browser tab.
                  </div>
                </div>
                <a href="#" target="_blank" rel="noopener noreferrer" class="btn-open-external-primary" id="fallback-main-ext-btn">
                  Open Original Website ↗
                </a>
              </div>
              <div class="fallback-summary-card">
                <h4 class="fallback-article-title" id="fallback-card-title">Technical Reference</h4>
                <div class="fallback-article-snippet" id="fallback-card-snippet"></div>
                <div class="fallback-article-code-wrapper" id="fallback-card-code-wrap" style="display: none;">
                  <div class="code-box-header"><span>Code Snippet</span></div>
                  <pre class="search-result-code"><code id="fallback-card-code"></code></pre>
                </div>
              </div>
            </div>

            <!-- 4. Floating Selection Action Pill -->
            <div class="reader-selection-pill" id="reader-selection-pill">
              <button type="button" class="btn-pill-insert-evidence" title="Insert into Notebook">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                + Insert into Notebook
              </button>
              <button type="button" class="btn-pill-quote-dock" title="Copy to Dock">
                Quote to Dock
              </button>
            </div>
          </div>

          <!-- Study & Evidence Capture Dock -->
          <div class="study-evidence-dock">
            <div class="evidence-dock-header">
              <span class="dock-title">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                Study &amp; Evidence Capture
              </span>
              <button type="button" class="btn-toggle-evidence-dock" title="Toggle Dock">Hide</button>
            </div>
            <div class="evidence-dock-body">
              <div class="evidence-inputs-row">
                <div class="evidence-col">
                  <label class="evidence-label">Selected Quote / Evidence Material</label>
                  <textarea class="evidence-textarea quote-input" placeholder="Type or select text in the article above to quote..."></textarea>
                </div>
                <div class="evidence-col">
                  <label class="evidence-label">Personal Explanation / Note</label>
                  <textarea class="evidence-textarea note-input" placeholder="Explain this concept in your own words..."></textarea>
                </div>
              </div>
              <div class="evidence-actions-row">
                <button type="button" class="btn btn-primary btn-evidence-insert-quote" title="Insert formatted quotation, source URL, and note into notebook">
                  + Insert into Notebook
                </button>
                <button type="button" class="btn btn-outline btn-evidence-clear" title="Clear Quote and Note">
                  Clear
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. HISTORY VIEW -->
        <div class="devsearch-view" id="devsearch-view-history">
          <div class="devsearch-section-header">
            <span>Recent Search History</span>
            <button type="button" class="btn btn-sm btn-clear-history" title="Clear all history">Clear All</button>
          </div>
          <div class="devsearch-history-list"></div>
        </div>

        <!-- 4. SAVED VIEW -->
        <div class="devsearch-view" id="devsearch-view-saved">
          <div class="devsearch-section-header">
            <span>Saved Bookmarks &amp; Resources</span>
            <span class="saved-count-badge">0 saved</span>
          </div>
          <div class="devsearch-saved-list"></div>
        </div>

        <!-- 5. OFFLINE DOCS VIEW -->
        <div class="devsearch-view" id="devsearch-view-docs">
          <div class="devsearch-section-header">
            <span>Local Offline Documentation (FTS5)</span>
          </div>
          <p class="devsearch-docs-desc" style="padding: 10px 16px 4px; font-size: 12px; color: var(--text-muted); margin: 0;">
            Download documentation indexes to search full-text without internet access. Powered by SQLite FTS5.
          </p>
          <div class="devsearch-doc-indexes-list"></div>
        </div>

        <!-- 6. AI ASSISTANT / LLM ADD-ON VIEW -->
        <div class="devsearch-view" id="devsearch-view-llm">
          <div class="devsearch-section-header">
            <span>AI Assistant</span>
            <div class="llm-header-actions" style="display: flex; gap: 6px;">
              <button type="button" class="btn btn-sm btn-clear-llm-chat" title="Clear Chat History">Clear</button>
              <button type="button" class="btn btn-sm btn-toggle-llm-settings" title="Configure LLM System">Settings</button>
            </div>
          </div>

          <div class="llm-workspace-view">
            <!-- Active Status Banner -->
            <div class="llm-status-banner">
              <div class="llm-status-indicator">
                <span class="llm-status-dot"></span>
                <span class="llm-current-provider-label">Ollama (Local)</span>
                <span style="color: var(--text-muted); font-size: 11px;" class="llm-current-model-label">llama3</span>
              </div>
              <span style="font-size: 10px; color: var(--text-subtle);">Local / Cloud AI</span>
            </div>

            <!-- Collapsible Settings Drawer -->
            <div class="llm-config-drawer" id="llm-config-drawer">
              <div style="font-size: 11.5px; font-weight: 700; color: var(--text-primary); margin-bottom: 2px;">
                LLM Configuration
              </div>
              <div class="form-group" style="margin-bottom: 8px;">
                <label style="display: block; font-size: 11px; font-weight: 600; margin-bottom: 3px;">Provider System</label>
                <select id="llm-setting-provider" class="form-input" style="font-size: 12px; padding: 4px 6px;">
                  <option value="ollama">Ollama (Local &amp; Private - http://localhost:11434)</option>
                  <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                  <option value="gemini">Google Gemini (gemini-1.5-flash)</option>
                  <option value="custom">Custom OpenAI-Compatible (LM Studio / vLLM / OpenRouter)</option>
                </select>
              </div>
              <div class="form-group" style="margin-bottom: 8px;">
                <label style="display: block; font-size: 11px; font-weight: 600; margin-bottom: 3px;">Endpoint URL</label>
                <input type="text" id="llm-setting-endpoint" class="form-input" placeholder="http://localhost:11434" style="font-size: 12px; padding: 4px 6px;" />
              </div>
              <div class="form-group" style="margin-bottom: 8px;">
                <label style="display: block; font-size: 11px; font-weight: 600; margin-bottom: 3px;">Model Identifier</label>
                <input type="text" id="llm-setting-model" class="form-input" placeholder="llama3" style="font-size: 12px; padding: 4px 6px;" />
              </div>
              <div class="form-group" style="margin-bottom: 8px;">
                <label style="display: block; font-size: 11px; font-weight: 600; margin-bottom: 3px;">API Key (Optional for Ollama)</label>
                <input type="password" id="llm-setting-apikey" class="form-input" placeholder="sk-... or blank for local" style="font-size: 12px; padding: 4px 6px;" />
              </div>
              <div class="form-group" style="margin-bottom: 8px;">
                <label style="display: block; font-size: 11px; font-weight: 600; margin-bottom: 3px;">Assistant Persona</label>
                <select id="llm-setting-persona" class="form-input" style="font-size: 12px; padding: 4px 6px;">
                  <option value="developer">Expert Technical Pair Programmer</option>
                  <option value="notes">Concise Study Notes Generator</option>
                  <option value="tutor">Algorithm &amp; Mathematics Tutor</option>
                </select>
              </div>
              <div style="display: flex; gap: 8px; margin-top: 4px;">
                <button type="button" class="btn btn-sm btn-test-llm" style="font-size: 11.5px;">Test Connection</button>
                <button type="button" class="btn btn-primary btn-sm btn-save-llm-config" style="font-size: 11.5px;">Save Settings</button>
              </div>
              <div class="llm-test-feedback" style="font-size: 11px; margin-top: 4px; display: none;"></div>
            </div>

            <!-- Quick Action Prompt Chips (No Emojis) -->
            <div class="llm-quick-chips">
              <button type="button" class="llm-chip" data-action="explain-code">Explain Code Cell</button>
              <button type="button" class="llm-chip" data-action="summarize-notebook">Summarize Notebook</button>
              <button type="button" class="llm-chip" data-action="summarize-reader">Summarize Research</button>
              <button type="button" class="llm-chip" data-action="fix-bug">Debug / Fix Bug</button>
              <button type="button" class="llm-chip" data-action="generate-python">Python Solution</button>
            </div>

            <!-- Interactive Chat Messages Feed -->
            <div class="llm-chat-messages" id="llm-chat-messages">
              <div class="llm-msg llm-msg-assistant">
                <div class="llm-msg-content">
                  <strong>Welcome to DevNote AI Assistant</strong>
                  <p style="margin: 4px 0 0 0; font-size: 12px; color: var(--text-secondary);">
                    This assistant helps with code explanations, debugging, research summaries, and note generation. Connect local models via Ollama or LM Studio, or cloud providers (OpenAI, Gemini).
                  </p>
                  <p style="margin: 4px 0 0 0; font-size: 12px; color: var(--text-secondary);">
                    Click any action chip above or type your question below.
                  </p>
                </div>
              </div>
            </div>

            <!-- Prompt Input Bar -->
            <div class="llm-input-area">
              <div style="display: flex; align-items: center; justify-content: space-between; font-size: 11px; color: var(--text-muted); margin-bottom: 2px;">
                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                  <input type="checkbox" id="llm-attach-context" checked />
                  Attach active notebook / reader context
                </label>
                <span>Enter to send / Shift+Enter for newline</span>
              </div>
              <div class="llm-input-row">
                <textarea class="llm-textarea" id="llm-prompt-input" rows="1" placeholder="Ask assistant about code, concepts, or notes..."></textarea>
                <button type="button" class="btn-send-llm" id="btn-send-llm">Send</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 7. SETTINGS VIEW -->
        <div class="devsearch-view" id="devsearch-view-settings">
          <div class="devsearch-section-header">
            <span>DevSearch Provider Configuration</span>
          </div>
          <form class="devsearch-settings-form" style="padding: 14px 16px;">
            <div class="form-group" style="margin-bottom: 12px;">
              <label style="display: block; font-size: 12px; font-weight: 600; margin-bottom: 4px;">Default Search Provider</label>
              <select id="setting-default-provider" class="form-input">
                <option value="searxng">SearXNG Meta-Search (Default)</option>
                <option value="general">General Web &amp; Knowledge</option>
                <option value="all">Unified (All Sources)</option>
                <option value="devdocs">DevDocs / Official Docs</option>
                <option value="local_docs">Local Offline Docs (FTS5)</option>
                <option value="stackoverflow">Stack Overflow</option>
                <option value="github">GitHub</option>
              </select>
              <small class="form-hint" style="display: block; font-size: 11px; color: var(--text-muted); margin-top: 3px;">SearXNG serves as the primary default metasearch engine with zero Google API keys required.</small>
            </div>
            <div class="form-group" style="margin-bottom: 12px;">
              <label style="display: block; font-size: 12px; font-weight: 600; margin-bottom: 4px;">SearXNG Instance URL</label>
              <input type="text" id="setting-searxng-url" class="form-input" placeholder="http://localhost:8080" />
              <small class="form-hint" style="display: block; font-size: 11px; color: var(--text-muted); margin-top: 3px;">Configurable SearXNG JSON Search API endpoint (default: <code>http://localhost:8080</code> for local Docker instance). Supports General, IT, and Science search categories.</small>
            </div>
            <div class="form-group" style="margin-bottom: 12px;">
              <label style="display: block; font-size: 12px; font-weight: 600; margin-bottom: 4px;">GitHub Personal Access Token (Optional)</label>
              <input type="password" id="setting-github-token" class="form-input" placeholder="ghp_..." />
              <small class="form-hint" style="display: block; font-size: 11px; color: var(--text-muted); margin-top: 3px;">Increases GitHub API rate limit from 60 to 5,000 req/hr. Optional.</small>
            </div>
            <div class="form-group-checkbox" style="margin-bottom: 16px;">
              <label style="font-size: 12px; display: flex; align-items: center; gap: 6px;">
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
          <button type="button" class="btn-close-preview" title="Close Preview">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
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
    this.splitBtn = this.panel.querySelector(".btn-split-search");
    this.categoryTabs = this.panel.querySelectorAll(".search-tab-pill");
    this.langFilter = this.panel.querySelector("#search-filter-lang");
    this.fwFilter = this.panel.querySelector("#search-filter-fw");
    this.intentBanner = this.panel.querySelector(".search-intent-banner");
    this.navBtns = this.panel.querySelectorAll(".devsearch-nav-btn");
    this.views = this.panel.querySelectorAll(".devsearch-view");
    this.previewDrawer = this.panel.querySelector(".devsearch-preview-drawer");
    this.onlineBadge = this.panel.querySelector("#devsearch-online-badge");
    this.offlineBanner = this.panel.querySelector(".devsearch-offline-banner");

    // Research Browser & Reader Elements
    this.browserView = this.panel.querySelector("#devsearch-view-browser");
    this.browserBackResultsBtn = this.panel.querySelector(".btn-browser-back-results");
    this.browserNavBackBtn = this.panel.querySelector(".btn-browser-nav-back");
    this.browserNavFwdBtn = this.panel.querySelector(".btn-browser-nav-forward");
    this.browserNavReloadBtn = this.panel.querySelector(".btn-browser-nav-reload");
    this.browserUrlInput = this.panel.querySelector(".browser-url-input");
    this.readerStrategyPill = this.panel.querySelector("#reader-strategy-pill");
    this.readerFontDownBtn = this.panel.querySelector(".btn-reader-font-down");
    this.readerFontUpBtn = this.panel.querySelector(".btn-reader-font-up");
    this.readerWidthToggleBtn = this.panel.querySelector(".btn-reader-width-toggle");
    this.readerFindToggleBtn = this.panel.querySelector(".btn-reader-find-toggle");
    this.readerCopyCitationBtn = this.panel.querySelector(".btn-reader-copy-citation");
    this.browserCopyUrlBtn = this.panel.querySelector(".btn-browser-copy-url");
    this.browserBookmarkBtn = this.panel.querySelector(".btn-browser-bookmark");
    this.browserOpenExtBtn = this.panel.querySelector(".btn-browser-open-external");

    this.readerFindBar = this.panel.querySelector("#reader-find-bar");
    this.readerFindInput = this.panel.querySelector(".reader-find-input");
    this.readerFindCount = this.panel.querySelector(".reader-find-count");
    this.readerFindPrevBtn = this.panel.querySelector(".btn-find-prev");
    this.readerFindNextBtn = this.panel.querySelector(".btn-find-next");
    this.readerFindCloseBtn = this.panel.querySelector(".btn-find-close");

    this.readerFrameContainer = this.panel.querySelector("#reader-frame-container");
    this.readerNativeView = this.panel.querySelector("#reader-native-view");
    this.readerArticleHeader = this.panel.querySelector("#reader-article-header");
    this.readerArticleTitle = this.panel.querySelector("#reader-article-title");
    this.readerArticleMeta = this.panel.querySelector("#reader-article-meta");
    this.readerArticleBody = this.panel.querySelector("#reader-article-body");
    this.readerLoadingView = this.panel.querySelector("#reader-loading-view");
    this.readerFallbackView = this.panel.querySelector("#reader-fallback-view");

    this.fallbackStatusTitle = this.panel.querySelector("#fallback-status-title");
    this.fallbackStatusDesc = this.panel.querySelector("#fallback-status-desc");
    this.fallbackMainExtBtn = this.panel.querySelector("#fallback-main-ext-btn");
    this.fallbackCardTitle = this.panel.querySelector("#fallback-card-title");
    this.fallbackCardSnippet = this.panel.querySelector("#fallback-card-snippet");
    this.fallbackCardCodeWrap = this.panel.querySelector("#fallback-card-code-wrap");
    this.fallbackCardCode = this.panel.querySelector("#fallback-card-code");

    this.readerSelectionPill = this.panel.querySelector("#reader-selection-pill");
    this.pillInsertEvidenceBtn = this.panel.querySelector(".btn-pill-insert-evidence");
    this.pillQuoteDockBtn = this.panel.querySelector(".btn-pill-quote-dock");

    // Evidence Capture Dock Elements
    this.evidenceDock = this.panel.querySelector(".study-evidence-dock");
    this.evidenceToggleBtn = this.panel.querySelector(".btn-toggle-evidence-dock");
    this.quoteInput = this.panel.querySelector(".evidence-textarea.quote-input");
    this.noteInput = this.panel.querySelector(".evidence-textarea.note-input");
    this.insertQuoteBtn = this.panel.querySelector(".btn-evidence-insert-quote");
    this.insertRefBtn = this.panel.querySelector(".btn-evidence-insert-ref");
    this.insertCodeBtn = this.panel.querySelector(".btn-evidence-insert-code");
    this.insertAllBtn = this.panel.querySelector(".btn-evidence-insert-both");
  }

  attachEvents() {
    // 1. Live Debounced Search Input
    this.searchInput.addEventListener("input", (e) => {
      this.currentQuery = e.target.value;
      this.clearBtn.classList.toggle("visible", !!this.currentQuery);

      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.performSearch(this.currentQuery);
      }, 250);
    });

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

    // 3. Header Action Buttons
    this.closeBtn.addEventListener("click", () => this.toggleCollapse(true));
    this.expandBtn.addEventListener("click", () => this.toggleExpand());
    this.splitBtn.addEventListener("click", () => this.resetSplit());

    // 4. Category Tabs
    this.categoryTabs.forEach(tab => {
      tab.addEventListener("click", () => {
        this.categoryTabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        this.currentCategory = tab.dataset.category;
        this.performSearch(this.currentQuery);
      });
    });

    // 5. Language & Framework Filters (if present)
    if (this.langFilter) {
      this.langFilter.addEventListener("change", (e) => {
        this.currentLanguage = e.target.value;
        this.performSearch(this.currentQuery);
      });
    }
    if (this.fwFilter) {
      this.fwFilter.addEventListener("change", (e) => {
        this.currentFramework = e.target.value;
        this.performSearch(this.currentQuery);
      });
    }

    // Close on Escape key press
    this.panel.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        this.toggleCollapse(true);
      }
    });

    // 6. Navigation Tabs
    this.navBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        this.switchView(btn.dataset.view);
      });
    });

    // 7. Preview Drawer Close
    const closePreviewBtn = this.previewDrawer.querySelector(".btn-close-preview");
    if (closePreviewBtn) {
      closePreviewBtn.addEventListener("click", () => this.closePreview());
    }

    // 8. Research Reader Navigation & History Controls
    this.browserBackResultsBtn.addEventListener("click", () => {
      if (this.currentBrowserItem) {
        this.currentBrowserItem = null;
        this.renderReaderSearchHub();
      } else {
        this.switchView("search");
      }
    });

    this.browserNavBackBtn.addEventListener("click", () => {
      if (this.readerHistoryIndex > 0) {
        this.readerHistoryIndex--;
        const hist = this.readerHistory[this.readerHistoryIndex];
        if (hist) {
          this.currentBrowserItem = hist.item || this.currentBrowserItem;
          this.loadUrlInBrowser(hist.url, false, false);
        }
      }
    });

    this.browserNavFwdBtn.addEventListener("click", () => {
      if (this.readerHistoryIndex < this.readerHistory.length - 1) {
        this.readerHistoryIndex++;
        const hist = this.readerHistory[this.readerHistoryIndex];
        if (hist) {
          this.currentBrowserItem = hist.item || this.currentBrowserItem;
          this.loadUrlInBrowser(hist.url, false, false);
        }
      }
    });

    this.browserNavReloadBtn.addEventListener("click", () => {
      const url = this.browserUrlInput.value.trim();
      if (url) {
        this.loadUrlInBrowser(url, true, false);
      }
    });

    this.browserUrlInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        let input = this.browserUrlInput.value.trim();
        if (!input) return;

        // Omnibox: check if input is a valid URL/domain or a raw text search query
        const isLikelyUrl = /^https?:\/\//i.test(input) || 
          (/^localhost(:\d+)?(\/.*)?$/i.test(input)) ||
          (/^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+(\/.*)?$/i.test(input) && !input.includes(" "));

        if (isLikelyUrl) {
          let url = input;
          if (!url.startsWith("http://") && !url.startsWith("https://")) {
            url = `https://${url}`;
            this.browserUrlInput.value = url;
          }
          this.loadUrlInBrowser(url, false, true);
        } else {
          // Input is RAW TEXT -> Execute General Search right in the Reader Hub!
          this.renderReaderSearchHub(input);
        }
      }
    });

    // Reader Font Size Controls
    this.readerFontDownBtn.addEventListener("click", () => {
      if (this.readerFontSize > 11) {
        this.readerFontSize -= 1;
        this.readerNativeView.style.setProperty("--reader-font-size", `${this.readerFontSize}px`);
      }
    });

    this.readerFontUpBtn.addEventListener("click", () => {
      if (this.readerFontSize < 24) {
        this.readerFontSize += 1;
        this.readerNativeView.style.setProperty("--reader-font-size", `${this.readerFontSize}px`);
      }
    });

    // Reader Width Toggle
    this.readerWidthToggleBtn.addEventListener("click", () => {
      if (this.readerWidth === "standard") {
        this.readerWidth = "wide";
        this.readerNativeView.className = "research-reader-wrapper width-wide";
        this.readerWidthToggleBtn.title = "Reading Width: Wide (Click for Full)";
      } else if (this.readerWidth === "wide") {
        this.readerWidth = "full";
        this.readerNativeView.className = "research-reader-wrapper width-full";
        this.readerWidthToggleBtn.title = "Reading Width: Full (Click for Standard)";
      } else {
        this.readerWidth = "standard";
        this.readerNativeView.className = "research-reader-wrapper width-standard";
        this.readerWidthToggleBtn.title = "Reading Width: Standard (Click for Wide)";
      }
    });

    // In-page Find Bar Controls
    this.readerFindToggleBtn.addEventListener("click", () => {
      const isActive = this.readerFindBar.classList.toggle("active");
      if (isActive) {
        this.readerFindInput.focus();
        this.readerFindInput.select();
      } else {
        this.clearFindHighlights();
      }
    });

    this.readerFindInput.addEventListener("input", (e) => {
      this.runFindInPage(e.target.value);
    });

    this.readerFindInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        this.navigateFindMatch(e.shiftKey ? -1 : 1);
      } else if (e.key === "Escape") {
        this.readerFindBar.classList.remove("active");
        this.clearFindHighlights();
      }
    });

    this.readerFindNextBtn.addEventListener("click", () => this.navigateFindMatch(1));
    this.readerFindPrevBtn.addEventListener("click", () => this.navigateFindMatch(-1));
    this.readerFindCloseBtn.addEventListener("click", () => {
      this.readerFindBar.classList.remove("active");
      this.clearFindHighlights();
    });

    // Copy Citation
    this.readerCopyCitationBtn.addEventListener("click", () => this.copyCitation());

    this.browserCopyUrlBtn.addEventListener("click", () => {
      const url = this.browserUrlInput.value.trim();
      if (url) {
        navigator.clipboard.writeText(url);
        this.browserCopyUrlBtn.title = "Copied!";
        setTimeout(() => (this.browserCopyUrlBtn.title = "Copy URL"), 1500);
      }
    });

    this.browserBookmarkBtn.addEventListener("click", async () => {
      if (this.currentBrowserItem) {
        try {
          await API.saveBookmark({
            title: this.currentBrowserItem.title,
            snippet: this.quoteInput.value.trim() || this.currentBrowserItem.snippet,
            code: this.currentBrowserItem.code,
            language: this.currentBrowserItem.language,
            source: this.currentBrowserItem.source,
            url: this.browserUrlInput.value.trim() || this.currentBrowserItem.url,
            category: this.currentBrowserItem.category || "doc",
            folder: "General"
          });
          this.browserBookmarkBtn.style.color = "var(--success-text)";
          setTimeout(() => (this.browserBookmarkBtn.style.color = ""), 1500);
        } catch (_) {}
      }
    });

    // In-article hyperlink interception (smooth browsing inside reader)
    this.readerArticleBody.addEventListener("click", (e) => {
      const anchor = e.target.closest("a");
      if (!anchor) return;

      const href = anchor.getAttribute("href");
      if (!href) return;

      if (href.startsWith("#")) {
        // Anchor link on current page
        e.preventDefault();
        const targetId = href.substring(1);
        const targetEl = this.readerArticleBody.querySelector(`[id="${targetId}"], a[name="${targetId}"]`);
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: "smooth" });
        }
        return;
      }

      // Check external or normal page link
      e.preventDefault();
      let resolvedUrl = href;
      if (!href.startsWith("http://") && !href.startsWith("https://")) {
        try {
          const base = new URL(this.browserUrlInput.value || "https://example.com");
          resolvedUrl = new URL(href, base).href;
        } catch (_) {
          resolvedUrl = href;
        }
      }
      this.loadUrlInBrowser(resolvedUrl, false, true);
    });

    // Text selection on reader article body
    this.readerArticleBody.addEventListener("mouseup", () => this.handleTextSelection());
    this.readerArticleBody.addEventListener("keyup", () => this.handleTextSelection());

    document.addEventListener("selectionchange", () => {
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed || !this.readerArticleBody.contains(sel.anchorNode)) {
        if (this.readerSelectionPill.style.display === "flex") {
          setTimeout(() => {
            const activeSel = window.getSelection();
            if (!activeSel || activeSel.isCollapsed) {
              this.readerSelectionPill.style.display = "none";
            }
          }, 150);
        }
      }
    });

    // Floating Selection Pill Actions
    this.pillInsertEvidenceBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (this.selectedText) {
        const payload = {
          title: this.currentBrowserItem?.title || "Research Evidence",
          evidence: this.selectedText,
          snippet: this.selectedText,
          url: this.browserUrlInput.value.trim() || this.currentBrowserItem?.url || "",
          source: this.currentBrowserItem?.source || "Research Reader",
          note: ""
        };
        this.insertResultIntoNotebook(payload, "evidence");
        this.readerSelectionPill.style.display = "none";
        window.getSelection()?.removeAllRanges();
      }
    });

    this.pillQuoteDockBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (this.selectedText) {
        this.quoteInput.value = this.selectedText;
        this.readerSelectionPill.style.display = "none";
        this.noteInput.focus();
      }
    });

    // 9. Study & Evidence Dock Controls
    this.evidenceToggleBtn.addEventListener("click", () => {
      const isCollapsed = this.evidenceDock.classList.toggle("collapsed");
      this.evidenceToggleBtn.textContent = isCollapsed ? "Show" : "Hide";
    });

    if (this.insertQuoteBtn) {
      this.insertQuoteBtn.addEventListener("click", () => {
        const item = this.getEvidencePayload();
        this.insertResultIntoNotebook(item, "evidence");
      });
    }

    const clearEvidenceBtn = this.panel.querySelector(".btn-evidence-clear");
    if (clearEvidenceBtn) {
      clearEvidenceBtn.addEventListener("click", () => {
        if (this.quoteInput) this.quoteInput.value = "";
        if (this.noteInput) this.noteInput.value = "";
      });
    }

    if (this.insertRefBtn) {
      this.insertRefBtn.addEventListener("click", () => {
        const item = this.getEvidencePayload();
        this.insertResultIntoNotebook(item, "reference");
      });
    }

    if (this.insertCodeBtn) {
      this.insertCodeBtn.addEventListener("click", () => {
        const item = this.getEvidencePayload();
        this.insertResultIntoNotebook(item, "code");
      });
    }

    if (this.insertAllBtn) {
      this.insertAllBtn.addEventListener("click", () => {
        const item = this.getEvidencePayload();
        this.insertResultIntoNotebook(item, "both");
      });
    }

    // 10. Global Shortcuts in Research Workspace
    window.addEventListener("keydown", (e) => {
      if (this.currentView === "browser") {
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "f") {
          e.preventDefault();
          this.readerFindBar.classList.add("active");
          this.readerFindInput.focus();
          this.readerFindInput.select();
        } else if (e.altKey && e.key === "ArrowLeft") {
          e.preventDefault();
          if (this.browserNavBackBtn && !this.browserNavBackBtn.disabled) {
            this.browserNavBackBtn.click();
          }
        } else if (e.altKey && e.key === "ArrowRight") {
          e.preventDefault();
          if (this.browserNavFwdBtn && !this.browserNavFwdBtn.disabled) {
            this.browserNavFwdBtn.click();
          }
        }
      }
    });

    // 11. Online / Offline Network Status Listeners
    window.addEventListener("online", () => this.updateOnlineStatus());
    window.addEventListener("offline", () => this.updateOnlineStatus());

    // 12. Draggable Resizer
    if (this.resizer) {
      this.initDraggableResizer();
    }
  }

  // ------------------------------------------
  // Integrated Research Reader Methods
  // ------------------------------------------
  openInResearchBrowser(item) {
    this.currentBrowserItem = item;
    const url = item.url || "";

    this.browserUrlInput.value = url;
    this.browserOpenExtBtn.href = url || "#";
    this.fallbackMainExtBtn.href = url || "#";

    // Setup Fallback Information
    this.fallbackCardTitle.textContent = item.title || "Technical Reference";
    this.fallbackCardSnippet.textContent = item.snippet || "No description provided.";
    if (item.code) {
      this.fallbackCardCodeWrap.style.display = "block";
      this.fallbackCardCode.textContent = item.code;
    } else {
      this.fallbackCardCodeWrap.style.display = "none";
    }

    // Populate Study & Evidence Capture Dock
    this.quoteInput.value = item.snippet || "";
    this.noteInput.value = "";
    if (this.insertCodeBtn) {
      this.insertCodeBtn.style.display = item.code ? "inline-flex" : "none";
    }

    // Switch to Browser / Reader View
    this.switchView("browser");

    // Load extracted reader content
    this.loadUrlInBrowser(url, false, true);
  }

  async loadUrlInBrowser(url, forceRefresh = false, addToHistory = true) {
    if (!url || url === "#") {
      if (this.currentBrowserItem && (this.currentBrowserItem.snippet || this.currentBrowserItem.code)) {
        this.renderItemInNativeReader(this.currentBrowserItem);
        return;
      }
      this.renderReaderSearchHub();
      return;
    }

    this.browserUrlInput.value = url;
    this.browserOpenExtBtn.href = url;
    this.fallbackMainExtBtn.href = url;

    // History tracking
    if (addToHistory) {
      if (this.readerHistoryIndex < this.readerHistory.length - 1) {
        this.readerHistory = this.readerHistory.slice(0, this.readerHistoryIndex + 1);
      }
      this.readerHistory.push({ url, item: this.currentBrowserItem });
      this.readerHistoryIndex = this.readerHistory.length - 1;
    }
    this.updateHistoryNavButtons();

    // Show loading skeleton
    this.readerLoadingView.style.display = "flex";
    this.readerNativeView.style.display = "none";
    this.readerFallbackView.style.display = "none";
    this.readerSelectionPill.style.display = "none";
    this.clearFindHighlights();

    try {
      const data = await API.readResearchContent(url, forceRefresh);

      this.readerLoadingView.style.display = "none";

      if (data.status === "restricted" || data.status === "error" || !data.content_html) {
        if (this.currentBrowserItem && (this.currentBrowserItem.snippet || this.currentBrowserItem.code)) {
          this.renderItemInNativeReader(this.currentBrowserItem, data.error_message);
          return;
        }

        this.showFallbackView(
          data.title || (this.currentBrowserItem ? this.currentBrowserItem.title : "External Technical Resource"),
          data.error_message || "This website restricts in-app content extraction. You can open the official documentation directly in your browser."
        );
        this.updateStrategyPill("restricted", "External Only");
        return;
      }

      // Success or partial extraction
      this.readerNativeView.style.display = "block";
      this.readerFallbackView.style.display = "none";

      // Update Strategy Pill
      const strat = data.reading_strategy || "article";
      const stratLabels = {
        api: "GitHub API",
        doc: "Official Docs",
        article: "Web Reader",
        fallback: "Fallback"
      };
      this.updateStrategyPill(strat, stratLabels[strat] || "Native Reader");

      // Render Title & Metadata
      this.readerArticleTitle.textContent = data.title || (this.currentBrowserItem && this.currentBrowserItem.title) || "Technical Documentation";

      let metaHtml = `
        <span class="reader-meta-item">
          <a href="${this.escapeHTML(data.canonical_url || data.url)}" target="_blank" rel="noopener noreferrer" class="reader-meta-link">
            ${this.escapeHTML(data.source_name || "Source")}
          </a>
        </span>
      `;

      if (data.author) {
        metaHtml += `<span class="reader-meta-item">${this.escapeHTML(data.author)}</span>`;
      }
      if (data.published_at) {
        metaHtml += `<span class="reader-meta-item">${this.escapeHTML(data.published_at.slice(0, 10))}</span>`;
      }
      if (data.raw_text) {
        const wordCount = data.raw_text.trim().split(/\s+/).length;
        const readMins = Math.max(1, Math.round(wordCount / 200));
        metaHtml += `<span class="reader-meta-item">${readMins} min read</span>`;
      }

      this.readerArticleMeta.innerHTML = metaHtml;

      // Render Body Content
      this.readerArticleBody.innerHTML = data.content_html || "<p>No content extracted.</p>";

      // Process code blocks inside reader article body
      this.enhanceReaderCodeBlocks();

      // Update current browser item & evidence dock
      const firstCode = (data.code_snippets && data.code_snippets.length > 0) ? data.code_snippets[0] : null;
      this.currentBrowserItem = {
        title: data.title,
        url: data.canonical_url || data.url,
        snippet: (data.raw_text || "").slice(0, 300),
        source: data.source_name,
        code: firstCode ? firstCode.code : (this.currentBrowserItem ? this.currentBrowserItem.code : null),
        language: firstCode ? firstCode.language : "python",
        category: "doc"
      };

      if (!this.quoteInput.value.trim() && data.raw_text) {
        this.quoteInput.value = data.raw_text.slice(0, 250) + "...";
      }

      if (firstCode && this.insertCodeBtn) {
        this.insertCodeBtn.style.display = "inline-flex";
      }

      // Scroll reader to top
      this.readerNativeView.scrollTop = 0;

    } catch (err) {
      this.readerLoadingView.style.display = "none";
      if (this.currentBrowserItem && (this.currentBrowserItem.snippet || this.currentBrowserItem.code)) {
        this.renderItemInNativeReader(this.currentBrowserItem, err.message);
        return;
      }
      this.showFallbackView(
        "Extraction Error",
        `Could not retrieve content: ${err.message}. You can open the original website in a new tab.`
      );
      this.updateStrategyPill("restricted", "Offline / Error");
    }
  }

  enhanceReaderCodeBlocks() {
    const preBlocks = this.readerArticleBody.querySelectorAll("pre");
    preBlocks.forEach((pre) => {
      if (pre.closest(".reader-code-block-wrapper")) return;

      const codeEl = pre.querySelector("code") || pre;
      const codeText = codeEl.textContent || "";
      if (!codeText.trim()) return;

      // Detect language from class e.g. class="language-python"
      let lang = "code";
      const classes = (codeEl.className || "").split(/\s+/);
      for (const c of classes) {
        if (c.startsWith("language-")) {
          lang = c.replace("language-", "");
          break;
        }
      }

      const wrapper = document.createElement("div");
      wrapper.className = "reader-code-block-wrapper";

      const header = document.createElement("div");
      header.className = "reader-code-header";
      header.innerHTML = `
        <span class="reader-code-lang">${this.escapeHTML(lang)}</span>
        <div class="reader-code-actions">
          <button type="button" class="btn-reader-code btn-copy-reader-code">Copy</button>
          <button type="button" class="btn-reader-code btn-insert-reader-code">+ Insert Code</button>
        </div>
      `;

      pre.parentNode.insertBefore(wrapper, pre);
      wrapper.appendChild(header);
      wrapper.appendChild(pre);

      const copyBtn = header.querySelector(".btn-copy-reader-code");
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(codeText);
        copyBtn.textContent = "Copied!";
        setTimeout(() => (copyBtn.textContent = "Copy"), 1500);
      });

      const insertBtn = header.querySelector(".btn-insert-reader-code");
      insertBtn.addEventListener("click", () => {
        this.insertResultIntoNotebook({
          title: this.currentBrowserItem?.title || "Code Snippet",
          code: codeText,
          language: lang,
          url: this.browserUrlInput.value.trim() || "",
          source: this.currentBrowserItem?.source || "Research Reader"
        }, "code");
      });
    });
  }

  showFallbackView(title, message) {
    this.readerNativeView.style.display = "none";
    this.readerLoadingView.style.display = "none";
    this.readerFallbackView.style.display = "flex";

    this.fallbackStatusTitle.textContent = title;
    this.fallbackStatusDesc.textContent = message;

    if (this.currentBrowserItem) {
      this.fallbackCardTitle.textContent = this.currentBrowserItem.title || "Technical Reference";
      this.fallbackCardSnippet.textContent = this.currentBrowserItem.snippet || "";
      if (this.currentBrowserItem.code) {
        this.fallbackCardCodeWrap.style.display = "block";
        this.fallbackCardCode.textContent = this.currentBrowserItem.code;
      } else {
        this.fallbackCardCodeWrap.style.display = "none";
      }
    }
  }

  renderItemInNativeReader(item, notice = null) {
    if (!item) return;
    this.currentBrowserItem = item;
    this.readerLoadingView.style.display = "none";
    this.readerFallbackView.style.display = "none";
    this.readerNativeView.style.display = "block";

    const url = item.url || "";
    this.browserUrlInput.value = url;
    this.browserOpenExtBtn.href = url || "#";
    this.fallbackMainExtBtn.href = url || "#";

    this.readerArticleTitle.textContent = item.title || "Technical Document";

    let metaHtml = `<span class="reader-meta-item">Source: ${this.escapeHTML(item.source || "DevSearch")}</span>`;
    if (item.category) {
      metaHtml += `<span class="reader-meta-item">Category: ${this.escapeHTML(item.category)}</span>`;
    }
    if (url && url !== "#") {
      metaHtml += `<a class="reader-meta-item reader-external-link" href="${this.escapeHTML(url)}" target="_blank" rel="noopener noreferrer">Visit Original Site &nearr;</a>`;
    }
    this.readerArticleMeta.innerHTML = metaHtml;

    let bodyHtml = "";
    if (notice) {
      bodyHtml += `<div class="reader-notice-box" style="margin-bottom: 1rem; padding: 0.75rem 1rem; border-radius: 6px; background: var(--bg-secondary, #252526); border-left: 3px solid var(--accent, #3b82f6); font-size: 0.85rem; color: var(--text-secondary, #9ca3af);">
        ${this.escapeHTML(notice)}
      </div>`;
    }

    if (item.snippet) {
      bodyHtml += `<div class="reader-lead-paragraph" style="font-size: 0.95rem; line-height: 1.6; color: var(--text-primary, #e5e7eb); margin-bottom: 1.25rem;">${this.escapeHTML(item.snippet)}</div>`;
    }

    if (item.code) {
      const lang = item.language || "python";
      bodyHtml += `<pre><code class="language-${this.escapeHTML(lang)}">${this.escapeHTML(item.code)}</code></pre>`;
    }

    this.readerArticleBody.innerHTML = bodyHtml || "<p>No content preview available for this document.</p>";
    this.enhanceReaderCodeBlocks();

    this.updateStrategyPill("extracted", "Reader Preview");

    if (item.snippet && !this.quoteInput.value.trim()) {
      this.quoteInput.value = item.snippet.slice(0, 250);
    }
    if (item.code && this.insertCodeBtn) {
      this.insertCodeBtn.style.display = "inline-flex";
    }

    this.readerNativeView.scrollTop = 0;
  }

  renderReaderSearchHub(initialQuery = "") {
    this.currentBrowserItem = null;
    this.readerLoadingView.style.display = "none";
    this.readerFallbackView.style.display = "none";
    this.readerNativeView.style.display = "block";

    this.readerArticleTitle.textContent = "General Search & Research";
    this.readerArticleMeta.innerHTML = `
      <span class="reader-meta-item">Unified Multi-Source Engine</span>
      <span class="reader-meta-item">All Sources Active</span>
    `;

    this.updateStrategyPill("general", "General Search");

    const queryVal = initialQuery ? this.escapeHTML(initialQuery) : "";
    if (initialQuery) {
      this.browserUrlInput.value = initialQuery;
    }

    this.readerArticleBody.innerHTML = `
      <div class="reader-search-hub">
        <p class="reader-hub-subtitle" style="font-size: 0.88rem; color: var(--text-secondary, #9ca3af); margin-bottom: 1rem; line-height: 1.5;">
          Search technical topics across General Web, Official Docs, Stack Overflow, GitHub, DevDocs, Wikipedia, and Local Offline Documentation.
        </p>

        <div class="reader-hub-input-row" style="display: flex; gap: 8px; margin-bottom: 1rem;">
          <input type="text" id="reader-hub-query-input" class="search-input-box" style="flex: 1;" placeholder="Enter programming language, library, concept, or error..." value="${queryVal}" />
          <button type="button" id="reader-hub-submit-btn" class="btn btn-primary" style="padding: 0 16px; font-weight: 500;">Search All Sources</button>
        </div>

        <div class="reader-hub-topics" style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 1.25rem;">
          <span style="font-size: 0.78rem; color: var(--text-muted, #6b7280); align-self: center; margin-right: 4px;">Quick Topics:</span>
          <button type="button" class="search-tab-pill reader-topic-pill" data-query="Python asyncio concurrent tasks">Python Asyncio</button>
          <button type="button" class="search-tab-pill reader-topic-pill" data-query="FastAPI REST API tutorial">FastAPI</button>
          <button type="button" class="search-tab-pill reader-topic-pill" data-query="JavaScript Promise async await">JS Promises</button>
          <button type="button" class="search-tab-pill reader-topic-pill" data-query="Docker Compose multi-container">Docker</button>
          <button type="button" class="search-tab-pill reader-topic-pill" data-query="Binary Search Tree algorithm">Algorithms</button>
          <button type="button" class="search-tab-pill reader-topic-pill" data-query="Git rebase interactive">Git</button>
        </div>

        <div id="reader-hub-results" class="reader-hub-results-list" style="display: flex; flex-direction: column; gap: 12px;"></div>
      </div>
    `;

    const hubInput = this.readerArticleBody.querySelector("#reader-hub-query-input");
    const hubBtn = this.readerArticleBody.querySelector("#reader-hub-submit-btn");
    const topicPills = this.readerArticleBody.querySelectorAll(".reader-topic-pill");

    const triggerSearch = () => {
      const q = (hubInput?.value || "").trim();
      if (!q) return;
      this.browserUrlInput.value = q;
      this.executeReaderHubSearch(q);
    };

    if (hubBtn) {
      hubBtn.addEventListener("click", triggerSearch);
    }
    if (hubInput) {
      hubInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") triggerSearch();
      });
      if (!initialQuery) {
        setTimeout(() => hubInput.focus(), 50);
      }
    }

    topicPills.forEach(pill => {
      pill.addEventListener("click", () => {
        const q = pill.dataset.query;
        if (hubInput) hubInput.value = q;
        this.browserUrlInput.value = q;
        this.executeReaderHubSearch(q);
      });
    });

    if (initialQuery) {
      this.executeReaderHubSearch(initialQuery);
    }
  }

  async executeReaderHubSearch(query) {
    const resultsContainer = this.readerArticleBody.querySelector("#reader-hub-results");
    if (!resultsContainer) return;

    resultsContainer.innerHTML = `
      <div class="search-state-empty" style="padding: 2rem 0; text-align: center;">
        <div class="search-spinner" style="margin: 0 auto 10px;"></div>
        <span style="font-size: 0.88rem; color: var(--text-secondary, #9ca3af);">Searching all sources for "${this.escapeHTML(query)}"...</span>
      </div>
    `;

    try {
      const payload = {
        query: query.trim(),
        category: "all",
        limit: 25
      };

      const data = await API.unifiedSearch(payload);
      const results = data.results || [];

      if (results.length === 0) {
        resultsContainer.innerHTML = `
          <div class="search-state-empty" style="padding: 2rem 0; text-align: center;">
            <span style="font-size: 0.88rem; color: var(--text-secondary, #9ca3af);">No results found across developer sources for "${this.escapeHTML(query)}".</span>
          </div>
        `;
        return;
      }

      resultsContainer.innerHTML = "";

      results.forEach(item => {
        const card = document.createElement("div");
        card.className = "search-result-card";
        card.style.cursor = "default";

        const cat = (item.category || "").toLowerCase();
        const catBadgeClass =
          cat === "stackoverflow" ? "badge-so" :
          cat === "github" ? "badge-gh" :
          cat === "wikipedia" ? "badge-doc" :
          cat === "hackernews" ? "badge-warning" :
          cat === "doc" ? "badge-doc" : "badge-general";

        const sourceLabel = item.source || item.provider || "General Web";

        let codePreviewHtml = "";
        if (item.code) {
          const lang = item.language || "code";
          codePreviewHtml = `
            <div class="search-result-code-preview">
              <span class="code-preview-lang">${this.escapeHTML(lang)}</span>
              <pre><code>${this.escapeHTML(item.code.slice(0, 400))}</code></pre>
            </div>
          `;
        }

        card.innerHTML = `
          <div class="search-result-header">
            <span class="search-badge ${catBadgeClass}">${this.escapeHTML(sourceLabel)}</span>
            <span class="search-result-url">${this.escapeHTML(item.url || "")}</span>
          </div>
          <h4 class="search-result-title" style="cursor: pointer; color: var(--accent, #3b82f6);">${this.escapeHTML(item.title || "Untitled Resource")}</h4>
          <p class="search-result-snippet">${this.escapeHTML(item.snippet || "")}</p>
          ${codePreviewHtml}
          <div class="search-result-actions" style="margin-top: 8px; display: flex; gap: 8px;">
            <button type="button" class="btn btn-xs btn-reader-hub-open" style="background: var(--accent, #3b82f6); color: #fff; font-weight: 500;">Read in Reader</button>
            <button type="button" class="btn btn-xs btn-reader-hub-insert">+ Insert into Notebook</button>
            ${item.url ? `<a href="${this.escapeHTML(item.url)}" target="_blank" rel="noopener noreferrer" class="btn btn-xs btn-ghost" style="text-decoration: none;">Open ↗</a>` : ""}
          </div>
        `;

        const titleEl = card.querySelector(".search-result-title");
        const readBtn = card.querySelector(".btn-reader-hub-open");
        const insertBtn = card.querySelector(".btn-reader-hub-insert");

        const openDoc = () => this.openInResearchBrowser(item);

        titleEl.addEventListener("click", openDoc);
        readBtn.addEventListener("click", openDoc);
        insertBtn.addEventListener("click", () => {
          this.insertResultIntoNotebook(item, "all");
        });

        resultsContainer.appendChild(card);
      });

    } catch (err) {
      resultsContainer.innerHTML = `
        <div class="search-state-empty" style="color: var(--error-text, #ef4444); padding: 1.5rem 0; text-align: center;">
          <span>Search failed: ${this.escapeHTML(err.message)}</span>
        </div>
      `;
    }
  }

  updateStrategyPill(strategy, label) {
    if (!this.readerStrategyPill) return;
    this.readerStrategyPill.className = `reader-strategy-pill ${strategy}`;
    this.readerStrategyPill.textContent = label;
  }

  updateHistoryNavButtons() {
    if (this.browserNavBackBtn) {
      this.browserNavBackBtn.disabled = this.readerHistoryIndex <= 0;
    }
    if (this.browserNavFwdBtn) {
      this.browserNavFwdBtn.disabled = this.readerHistoryIndex >= this.readerHistory.length - 1;
    }
  }

  handleTextSelection() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) {
      this.readerSelectionPill.style.display = "none";
      return;
    }

    const text = sel.toString().trim();
    if (text.length < 3) {
      this.readerSelectionPill.style.display = "none";
      return;
    }

    this.selectedText = text;

    try {
      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      const containerRect = this.readerFrameContainer.getBoundingClientRect();

      const top = Math.max(10, rect.top - containerRect.top - 38);
      const left = Math.max(80, Math.min(containerRect.width - 80, rect.left - containerRect.left + rect.width / 2));

      this.readerSelectionPill.style.top = `${top}px`;
      this.readerSelectionPill.style.left = `${left}px`;
      this.readerSelectionPill.style.display = "flex";
    } catch (_) {
      this.readerSelectionPill.style.display = "none";
    }
  }

  copyCitation() {
    const item = this.currentBrowserItem || {};
    const title = item.title || "Technical Documentation";
    const source = item.source || "DevSearch";
    const url = this.browserUrlInput.value.trim() || item.url || "";
    const today = new Date().toISOString().slice(0, 10);

    const citation = `"${title}". ${source}. ${url ? `Available at: <${url}>.` : ""} (Retrieved: ${today}).`;
    navigator.clipboard.writeText(citation);

    this.readerCopyCitationBtn.title = "Citation Copied!";
    setTimeout(() => {
      this.readerCopyCitationBtn.title = "Copy Formatted Citation";
    }, 1500);
  }

  clearFindHighlights() {
    this.readerSearchMatches = [];
    this.currentMatchIndex = -1;
    if (this.readerFindCount) this.readerFindCount.textContent = "0 / 0";

    const marks = this.readerArticleBody.querySelectorAll("mark.reader-search-highlight");
    marks.forEach(m => {
      const parent = m.parentNode;
      if (parent) {
        parent.replaceChild(document.createTextNode(m.textContent), m);
        parent.normalize();
      }
    });
  }

  runFindInPage(keyword) {
    this.clearFindHighlights();
    const q = (keyword || "").trim();
    if (!q || q.length < 2) return;

    const regex = new RegExp(`(${q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, "gi");

    const walk = (node) => {
      if (node.nodeType === 3) { // text node
        const val = node.nodeValue;
        if (regex.test(val)) {
          const span = document.createElement("span");
          span.innerHTML = val.replace(regex, `<mark class="reader-search-highlight">$1</mark>`);
          node.parentNode.replaceChild(span, node);
        }
      } else if (node.nodeType === 1 && node.nodeName !== "SCRIPT" && node.nodeName !== "STYLE" && node.nodeName !== "MARK") {
        Array.from(node.childNodes).forEach(walk);
      }
    };

    walk(this.readerArticleBody);

    this.readerSearchMatches = Array.from(this.readerArticleBody.querySelectorAll("mark.reader-search-highlight"));
    const count = this.readerSearchMatches.length;

    if (count > 0) {
      this.currentMatchIndex = 0;
      this.readerFindCount.textContent = `1 / ${count}`;
      this.highlightCurrentMatch();
    } else {
      this.readerFindCount.textContent = "0 / 0";
    }
  }

  navigateFindMatch(dir) {
    if (this.readerSearchMatches.length === 0) return;
    this.currentMatchIndex = (this.currentMatchIndex + dir + this.readerSearchMatches.length) % this.readerSearchMatches.length;
    this.readerFindCount.textContent = `${this.currentMatchIndex + 1} / ${this.readerSearchMatches.length}`;
    this.highlightCurrentMatch();
  }

  highlightCurrentMatch() {
    this.readerSearchMatches.forEach((m, idx) => {
      m.classList.toggle("current", idx === this.currentMatchIndex);
    });
    const cur = this.readerSearchMatches[this.currentMatchIndex];
    if (cur) {
      cur.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  getEvidencePayload() {
    const quote = this.quoteInput.value.trim();
    const note = this.noteInput.value.trim();
    const base = this.currentBrowserItem || {};

    return {
      title: base.title || "Developer Research Reference",
      snippet: base.snippet || quote,
      evidence: quote,
      note: note,
      url: this.browserUrlInput.value.trim() || base.url || "",
      source: base.source || "DevSearch",
      code: base.code || null,
      language: base.language || "python",
      category: base.category || "doc",
    };
  }

  updateOnlineStatus() {
    const isOnline = navigator.onLine;
    if (this.onlineBadge) {
      this.onlineBadge.className = `devsearch-status-pill ${isOnline ? "online" : "offline"}`;
      this.onlineBadge.textContent = isOnline ? "Online" : "Offline";
    }
    if (this.offlineBanner) {
      this.offlineBanner.style.display = isOnline ? "none" : "flex";
    }
  }

  restoreSavedLayout() {
    const savedWidth = localStorage.getItem("devnote_research_panel_width");
    const savedState = localStorage.getItem("devnote_research_layout_state");

    if (savedWidth) {
      this.panel.style.width = savedWidth;
    } else {
      this.panel.style.width = "450px";
    }

    if (savedState === "expanded") {
      this.panel.classList.add("expanded");
      this.panel.style.width = "100%";
      this.isExpanded = true;
      if (this.expandBtn) this.expandBtn.classList.add("active");
    } else if (savedState === "split") {
      this.panel.classList.remove("collapsed");
      if (this.resizer) this.resizer.style.display = "block";
    } else {
      this.toggleCollapse(true);
    }
  }

  switchView(viewName) {
    this.currentView = viewName;
    this.navBtns.forEach(b => b.classList.toggle("active", b.dataset.view === viewName));
    this.views.forEach(v => v.classList.remove("active"));

    const target = this.panel.querySelector(`#devsearch-view-${viewName}`);
    if (target) target.classList.add("active");

    if (viewName === "history") this.loadHistory();
    else if (viewName === "saved") this.loadSavedResources();
    else if (viewName === "docs") this.loadDocIndexes();
    else if (viewName === "llm") this.loadLLMAssistant();
    else if (viewName === "settings") this.loadSettings();
    else if (viewName === "browser" && !this.currentBrowserItem) {
      this.renderReaderSearchHub();
    }
  }

  initDraggableResizer() {
    const onPointerDown = (e) => {
      e.preventDefault();
      this.isDragging = true;
      this.panel.classList.add("resizing");
      this.resizer.classList.add("dragging");
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";

      const onPointerMove = (moveEvt) => {
        if (!this.isDragging) return;
        const workspaceRect = document.getElementById("workspace-container").getBoundingClientRect();
        const minPx = 320;
        const maxPx = Math.max(minPx, workspaceRect.width * 0.85);
        const calculatedPx = Math.max(minPx, Math.min(maxPx, moveEvt.clientX - workspaceRect.left));

        this.panel.style.width = `${calculatedPx}px`;
        this.panel.classList.remove("expanded");
        this.isExpanded = false;
        if (this.expandBtn) this.expandBtn.classList.remove("active");
      };

      const onPointerUp = () => {
        if (this.isDragging) {
          this.isDragging = false;
          this.panel.classList.remove("resizing");
          this.resizer.classList.remove("dragging");
          document.body.style.cursor = "";
          document.body.style.userSelect = "";

          window.removeEventListener("pointermove", onPointerMove);
          window.removeEventListener("pointerup", onPointerUp);

          // Save preference
          localStorage.setItem("devnote_research_panel_width", this.panel.style.width);
          localStorage.setItem("devnote_research_layout_state", "split");
        }
      };

      window.addEventListener("pointermove", onPointerMove);
      window.addEventListener("pointerup", onPointerUp);
    };

    this.resizer.addEventListener("pointerdown", onPointerDown);
  }

  toggleExpand() {
    this.isExpanded = !this.isExpanded;
    if (this.isExpanded) {
      this.panel.classList.add("expanded");
      this.panel.style.width = "100%";
      this.expandBtn.classList.add("active");
      localStorage.setItem("devnote_research_layout_state", "expanded");
    } else {
      this.panel.classList.remove("expanded");
      const savedWidth = localStorage.getItem("devnote_research_panel_width") || "50%";
      this.panel.style.width = savedWidth;
      this.expandBtn.classList.remove("active");
      localStorage.setItem("devnote_research_layout_state", "split");
    }
  }

  resetSplit() {
    this.isExpanded = false;
    this.panel.classList.remove("expanded");
    this.panel.style.width = "50%";
    if (this.expandBtn) this.expandBtn.classList.remove("active");
    localStorage.setItem("devnote_research_panel_width", "50%");
    localStorage.setItem("devnote_research_layout_state", "split");
  }

  toggleCollapse(forceCollapse = null) {
    const isCurrentlyCollapsed = this.panel.classList.contains("collapsed");
    const shouldCollapse = forceCollapse !== null ? forceCollapse : !isCurrentlyCollapsed;

    this.panel.classList.toggle("collapsed", shouldCollapse);
    if (this.resizer) {
      this.resizer.style.display = shouldCollapse ? "none" : "block";
    }

    if (shouldCollapse) {
      localStorage.setItem("devnote_research_layout_state", "collapsed");
    } else {
      localStorage.setItem("devnote_research_layout_state", "split");
      setTimeout(() => this.searchInput.focus(), 50);
    }
  }

  isOpen() {
    return !this.panel.classList.contains("collapsed");
  }

  async performSearch(query) {
    try {
      if (this.activeAbortController) {
        this.activeAbortController.abort();
      }
      this.activeAbortController = new AbortController();

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

      // Hide extra classification banner for clean, minimal UI
      if (this.intentBanner) {
        this.intentBanner.style.display = "none";
      }

      this.renderResults(data.results || []);
    } catch (err) {
      if (err.name === "AbortError") return;
      this.resultsList.innerHTML = `
        <div class="search-state-empty" style="color: var(--error-text);">
          <span>Search failed: ${this.escapeHTML(err.message)}</span>
        </div>
      `;
    }
  }

  renderResults(results) {
    if (results.length === 0) {
      if (!this.currentQuery || !this.currentQuery.trim()) {
        this.resultsList.innerHTML = `
          <div class="search-state-empty">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            <span style="font-weight: 500; margin-top: 8px;">Search developer documentation, code, and web sources</span>
          </div>
        `;
        return;
      }
      this.resultsList.innerHTML = `
        <div class="search-state-empty">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <span style="font-weight: 500; margin-top: 8px;">No results found for "${this.escapeHTML(this.currentQuery)}"</span>
        </div>
      `;
      return;
    }

    this.resultsList.innerHTML = "";

    results.forEach(item => {
      const card = document.createElement("div");
      card.className = "search-result-card";

      const cat = (item.category || "").toLowerCase();
      const catBadgeClass =
        cat === "stackoverflow" ? "badge-so" :
        cat === "github" ? "badge-gh" :
        cat === "wikipedia" ? "badge-doc" :
        cat === "hackernews" ? "badge-warning" :
        cat === "offline" ? "badge-offline" :
        cat === "doc" ? "badge-doc" :
        cat === "it" ? "badge-success" :
        cat === "science" ? "badge-primary" :
        cat === "general" || cat === "web" ? "badge-neutral" :
        cat === "error" ? "badge-warning" : "badge-neutral";

      const sourceLabel = item.source || cat.toUpperCase();

      card.innerHTML = `
        <div class="search-result-header">
          <div class="search-result-title cursor-pointer">${this.escapeHTML(item.title)}</div>
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
          ${item.stars ? `<span>${item.stars.toLocaleString()} stars</span>` : ""}
          ${item.score ? `<span>${item.score} votes</span>` : ""}
          ${item.is_answered ? `<span style="color: var(--success-text);">Accepted</span>` : ""}
          ${item.date ? `<span>${this.escapeHTML(item.date)}</span>` : ""}
        </div>
        <div class="search-result-footer">
          <span class="search-result-source">${this.escapeHTML(sourceLabel)}</span>
          <div class="search-card-actions">
            <button type="button" class="btn-card-action btn-study-browser" title="Read in Research Reader">Read</button>
            <button type="button" class="btn-card-action btn-insert-ref" title="Insert into notebook">+ Insert</button>
            <button type="button" class="btn-card-action btn-bookmark-action" title="Save Resource">Save</button>
            ${item.url ? `<a href="${this.escapeHTML(item.url)}" target="_blank" rel="noopener noreferrer" class="btn-card-action" title="Open external link">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>` : ""}
          </div>
        </div>
      `;

      // Click Title or Study -> Open in Research Reader
      card.querySelector(".search-result-title").addEventListener("click", () => {
        this.openInResearchBrowser(item);
      });

      card.querySelector(".btn-study-browser").addEventListener("click", () => {
        this.openInResearchBrowser(item);
      });

      // Copy Code
      const copyBtn = card.querySelector(".btn-copy-code");
      if (copyBtn && item.code) {
        copyBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          navigator.clipboard.writeText(item.code);
          copyBtn.textContent = "Copied";
          setTimeout(() => (copyBtn.textContent = "Copy"), 1500);
        });
      }

      // Action: Insert (Code if available, otherwise reference)
      card.querySelector(".btn-insert-ref").addEventListener("click", () => {
        this.insertResultIntoNotebook(item, item.code ? "both" : "reference");
      });

      // Bookmark Action
      const bookmarkBtn = card.querySelector(".btn-bookmark-action");
      bookmarkBtn.addEventListener("click", async () => {
        try {
          await API.saveBookmark({
            title: item.title,
            snippet: item.snippet,
            code: item.code,
            language: item.language,
            source: item.source,
            url: item.url,
            category: item.category,
            folder: "General"
          });
          bookmarkBtn.textContent = "Saved";
          bookmarkBtn.style.color = "var(--success-text)";
          setTimeout(() => {
            bookmarkBtn.textContent = "Save";
            bookmarkBtn.style.color = "";
          }, 1500);
        } catch (_) {}
      });

      this.resultsList.appendChild(card);
    });
  }

  // ------------------------------------------
  // Preview Drawer
  // ------------------------------------------
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
            <button type="button" class="btn-rerun-query" title="Run search again">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            </button>
            <button type="button" class="btn-del-history" title="Delete entry">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
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
  // Saved Resources & Bookmarks View
  // ------------------------------------------
  async loadSavedResources() {
    const list = this.panel.querySelector(".devsearch-saved-list");
    const countBadge = this.panel.querySelector(".saved-count-badge");
    list.innerHTML = `<div class="search-state-empty"><span>Loading bookmarks...</span></div>`;

    try {
      const saved = await API.getBookmarks();
      countBadge.textContent = `${saved.length} saved`;

      if (saved.length === 0) {
        list.innerHTML = `<div class="search-state-empty"><span>No bookmarked resources. Click Save on any search result to keep it here.</span></div>`;
        return;
      }

      list.innerHTML = "";
      saved.forEach(s => {
        const card = document.createElement("div");
        card.className = "search-result-card";
        card.innerHTML = `
          <div class="search-result-header">
            <div class="search-result-title cursor-pointer">${this.escapeHTML(s.title)}</div>
            <span class="badge badge-neutral">${this.escapeHTML(s.folder || "General")}</span>
          </div>
          <div class="search-result-snippet">${this.escapeHTML(s.snippet)}</div>
          ${s.code ? `<pre class="search-result-code"><code>${this.escapeHTML(s.code)}</code></pre>` : ""}
          <div class="search-result-footer">
            <span class="search-result-source">${this.escapeHTML(s.source || "Saved")}</span>
            <div class="search-card-actions">
              <button type="button" class="btn-card-action btn-study-saved" title="Read in Research Reader">Read</button>
              <button type="button" class="btn-card-action btn-insert-saved" title="Insert into active notebook">+ Insert</button>
              <button type="button" class="btn-card-action btn-del-saved" title="Remove bookmark">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>
          </div>
        `;

        card.querySelector(".search-result-title").addEventListener("click", () => {
          this.openInResearchBrowser(s);
        });

        card.querySelector(".btn-study-saved").addEventListener("click", () => {
          this.openInResearchBrowser(s);
        });

        card.querySelector(".btn-insert-saved").addEventListener("click", () => {
          this.insertResultIntoNotebook(s, "both");
        });

        card.querySelector(".btn-del-saved").addEventListener("click", async () => {
          await API.deleteBookmark(s.id);
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
              <span class="badge ${isDownloaded ? 'badge-success' : 'badge-neutral'}">${isDownloaded ? 'Downloaded' : 'Available'}</span>
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
      const searxngInput = this.panel.querySelector("#setting-searxng-url");
      const defaultProv = this.panel.querySelector("#setting-default-provider");
      const ghTokenInput = this.panel.querySelector("#setting-github-token");
      const cacheCheckbox = this.panel.querySelector("#setting-enable-cache");

      if (searxngInput) searxngInput.value = settings.searxng_url || "http://localhost:8080";
      if (defaultProv) defaultProv.value = settings.default_provider || "searxng";
      if (cacheCheckbox) cacheCheckbox.checked = settings.enable_cache !== false;

      const saveBtn = this.panel.querySelector(".btn-save-settings");
      saveBtn.onclick = async () => {
        saveBtn.textContent = "Saving...";
        const searxngUrl = searxngInput ? searxngInput.value.trim() : "";
        const ghToken = ghTokenInput ? ghTokenInput.value.trim() : "";

        const updateData = {
          default_provider: defaultProv ? defaultProv.value : "searxng",
          enable_cache: cacheCheckbox ? cacheCheckbox.checked : true,
          searxng_url: searxngUrl || "http://localhost:8080"
        };
        if (ghToken) updateData.github_token = ghToken;

        await API.updateSearchSettings(updateData);
        saveBtn.textContent = "Saved!";
        setTimeout(() => (saveBtn.textContent = "Save Settings"), 1500);
      };
    } catch (_) {}
  }

  // ------------------------------------------
  // LLM & AI Assistant Add-On
  // ------------------------------------------
  loadLLMAssistant() {
    const configDrawer = this.panel.querySelector("#llm-config-drawer");
    const toggleConfigBtn = this.panel.querySelector(".btn-toggle-llm-settings");
    const saveConfigBtn = this.panel.querySelector(".btn-save-llm-config");
    const testBtn = this.panel.querySelector(".btn-test-llm");
    const testFeedback = this.panel.querySelector(".llm-test-feedback");
    const clearChatBtn = this.panel.querySelector(".btn-clear-llm-chat");
    const sendBtn = this.panel.querySelector("#btn-send-llm");
    const promptInput = this.panel.querySelector("#llm-prompt-input");
    const chips = this.panel.querySelectorAll(".llm-chip");

    // Load saved settings from localStorage
    let settings = {};
    try {
      settings = JSON.parse(localStorage.getItem("devnote_llm_settings") || "{}");
    } catch (_) {}

    const providerSelect = this.panel.querySelector("#llm-setting-provider");
    const endpointInput = this.panel.querySelector("#llm-setting-endpoint");
    const modelInput = this.panel.querySelector("#llm-setting-model");
    const apiKeyInput = this.panel.querySelector("#llm-setting-apikey");
    const personaSelect = this.panel.querySelector("#llm-setting-persona");

    if (providerSelect && settings.provider) providerSelect.value = settings.provider;
    if (endpointInput && settings.endpoint) endpointInput.value = settings.endpoint;
    if (modelInput && settings.model) modelInput.value = settings.model;
    if (apiKeyInput && settings.apiKey) apiKeyInput.value = settings.apiKey;
    if (personaSelect && settings.persona) personaSelect.value = settings.persona;

    this.updateLLMStatusBanner(settings);

    if (!this._llmBound) {
      this._llmBound = true;

      if (toggleConfigBtn && configDrawer) {
        toggleConfigBtn.addEventListener("click", () => {
          configDrawer.classList.toggle("open");
        });
      }

      if (providerSelect) {
        providerSelect.addEventListener("change", () => {
          const prov = providerSelect.value;
          if (prov === "ollama") {
            endpointInput.value = "http://localhost:11434";
            modelInput.value = "llama3";
          } else if (prov === "openai") {
            endpointInput.value = "https://api.openai.com/v1";
            modelInput.value = "gpt-4o-mini";
          } else if (prov === "gemini") {
            endpointInput.value = "https://generativelanguage.googleapis.com";
            modelInput.value = "gemini-1.5-flash";
          } else if (prov === "custom") {
            endpointInput.value = "http://localhost:1234/v1";
            modelInput.value = "default";
          }
        });
      }

      if (saveConfigBtn) {
        saveConfigBtn.addEventListener("click", () => {
          const newSettings = {
            provider: providerSelect ? providerSelect.value : "ollama",
            endpoint: endpointInput ? endpointInput.value.trim() : "",
            model: modelInput ? modelInput.value.trim() : "llama3",
            apiKey: apiKeyInput ? apiKeyInput.value.trim() : "",
            persona: personaSelect ? personaSelect.value : "developer",
          };
          localStorage.setItem("devnote_llm_settings", JSON.stringify(newSettings));
          this.updateLLMStatusBanner(newSettings);
          if (configDrawer) configDrawer.classList.remove("open");
          if (testFeedback) {
            testFeedback.style.display = "block";
            testFeedback.style.color = "var(--success-text, #10b981)";
            testFeedback.textContent = "Settings saved successfully!";
            setTimeout(() => (testFeedback.style.display = "none"), 2000);
          }
        });
      }

      if (testBtn) {
        testBtn.addEventListener("click", async () => {
          if (!testFeedback) return;
          testFeedback.style.display = "block";
          testFeedback.style.color = "var(--text-muted)";
          testFeedback.textContent = "Connecting to LLM...";
          try {
            const res = await API.testLLMConnection({
              provider: providerSelect ? providerSelect.value : "ollama",
              endpoint: endpointInput ? endpointInput.value.trim() : "",
              model: modelInput ? modelInput.value.trim() : "",
              api_key: apiKeyInput ? apiKeyInput.value.trim() : ""
            });
            if (res.status === "ok") {
              testFeedback.style.color = "var(--success-text, #10b981)";
              testFeedback.textContent = `Connected! Latency: ${res.latency_ms || 0}ms`;
            } else {
              testFeedback.style.color = "var(--error-text, #ef4444)";
              testFeedback.textContent = `Connection failed: ${res.message || "Unknown error"}`;
            }
          } catch (err) {
            testFeedback.style.color = "var(--error-text, #ef4444)";
            testFeedback.textContent = `Error: ${err.message}`;
          }
        });
      }

      if (clearChatBtn) {
        clearChatBtn.addEventListener("click", () => {
          const chatContainer = this.panel.querySelector("#llm-chat-messages");
          if (chatContainer) {
            chatContainer.innerHTML = `
              <div class="llm-msg llm-msg-assistant">
                <div class="llm-msg-content">
                  <strong>Welcome to DevNote AI Assistant</strong>
                  <p style="margin: 4px 0 0 0; font-size: 12px; color: var(--text-secondary);">
                    Chat history cleared. How can I help you today?
                  </p>
                </div>
              </div>
            `;
          }
        });
      }

      if (sendBtn) {
        sendBtn.addEventListener("click", () => this.sendLLMChatMessage());
      }

      if (promptInput) {
        promptInput.addEventListener("keydown", (e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            this.sendLLMChatMessage();
          }
        });
      }

      chips.forEach((chip) => {
        chip.addEventListener("click", () => {
          const action = chip.dataset.action;
          this.handleLLMChipAction(action);
        });
      });
    }
  }

  updateLLMStatusBanner(settings) {
    const provLabel = this.panel.querySelector(".llm-current-provider-label");
    const modelLabel = this.panel.querySelector(".llm-current-model-label");
    const provMap = {
      ollama: "Ollama (Local)",
      openai: "OpenAI",
      gemini: "Google Gemini",
      custom: "Custom / LM Studio"
    };
    if (provLabel) provLabel.textContent = provMap[settings.provider || "ollama"] || "Ollama (Local)";
    if (modelLabel) modelLabel.textContent = settings.model || "llama3";
  }

  async sendLLMChatMessage(customPrompt = null) {
    const promptInput = this.panel.querySelector("#llm-prompt-input");
    const chatContainer = this.panel.querySelector("#llm-chat-messages");
    const attachContextCheckbox = this.panel.querySelector("#llm-attach-context");
    const sendBtn = this.panel.querySelector("#btn-send-llm");

    const prompt = customPrompt || (promptInput ? promptInput.value.trim() : "");
    if (!prompt) return;

    if (promptInput && !customPrompt) {
      promptInput.value = "";
      promptInput.style.height = "auto";
    }

    const userMsg = document.createElement("div");
    userMsg.className = "llm-msg llm-msg-user";
    userMsg.innerHTML = `<div class="llm-msg-content">${this.escapeHTML(prompt)}</div>`;
    chatContainer.appendChild(userMsg);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    let context = "";
    if (attachContextCheckbox && attachContextCheckbox.checked) {
      if (this.editor && this.editor.notebook) {
        const title = this.editor.notebook.title || "Untitled";
        const blocks = this.editor.notebook.blocks || [];
        const contentPieces = blocks.map(b => `[${b.type.toUpperCase()}]: ${b.content}`).join("\n\n");
        context += `Active Notebook: "${title}"\n${contentPieces}\n\n`;
      }
      if (this.currentBrowserItem) {
        context += `Active Research Document: "${this.currentBrowserItem.title || ''}" (${this.currentBrowserItem.url || ''})\n${this.currentBrowserItem.snippet || ''}\n`;
      }
    }

    let settings = {};
    try {
      settings = JSON.parse(localStorage.getItem("devnote_llm_settings") || "{}");
    } catch (_) {}

    const loadingMsg = document.createElement("div");
    loadingMsg.className = "llm-msg llm-msg-assistant";
    loadingMsg.innerHTML = `<div class="llm-msg-content" style="color: var(--text-muted); font-style: italic;">Thinking...</div>`;
    chatContainer.appendChild(loadingMsg);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    if (sendBtn) sendBtn.disabled = true;

    try {
      const payload = {
        prompt,
        provider: settings.provider || "ollama",
        endpoint: settings.endpoint || null,
        api_key: settings.apiKey || null,
        model: settings.model || null,
        context: context.trim() || null,
        temperature: 0.7
      };

      const res = await API.chatWithLLM(payload);
      const rawResponse = res.response || "No response received.";
      const formattedHTML = this.formatLLMResponseHTML(rawResponse);

      const codeMatch = rawResponse.match(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/);
      const extractedCode = codeMatch ? codeMatch[2] : null;
      const codeLang = codeMatch ? (codeMatch[1] || "python") : "python";

      loadingMsg.innerHTML = `
        <div class="llm-msg-content">${formattedHTML}</div>
        <div class="llm-msg-actions">
          <button type="button" class="btn-llm-action btn-insert-note">+ Insert Note</button>
          ${extractedCode ? `<button type="button" class="btn-llm-action btn-insert-code">+ Insert Code</button>` : ''}
          <button type="button" class="btn-llm-action btn-copy-response">Copy</button>
          <span style="margin-left: auto; font-size: 10px; color: var(--text-subtle);">
            ${this.escapeHTML(res.model || settings.model || "assistant")}
          </span>
        </div>
      `;

      loadingMsg.querySelector(".btn-insert-note").addEventListener("click", () => {
        if (this.editor) {
          this.editor.addBlock("markdown", rawResponse);
          const btn = loadingMsg.querySelector(".btn-insert-note");
          btn.textContent = "Inserted!";
          setTimeout(() => (btn.textContent = "+ Insert Note"), 1500);
        }
      });

      const insertCodeBtn = loadingMsg.querySelector(".btn-insert-code");
      if (insertCodeBtn && extractedCode) {
        insertCodeBtn.addEventListener("click", () => {
          if (this.editor) {
            this.editor.addBlock("code", extractedCode, codeLang);
            insertCodeBtn.textContent = "Inserted!";
            setTimeout(() => (insertCodeBtn.textContent = "+ Insert Code"), 1500);
          }
        });
      }

      loadingMsg.querySelector(".btn-copy-response").addEventListener("click", () => {
        navigator.clipboard.writeText(rawResponse);
        const btn = loadingMsg.querySelector(".btn-copy-response");
        btn.textContent = "Copied!";
        setTimeout(() => (btn.textContent = "Copy"), 1500);
      });

    } catch (err) {
      loadingMsg.innerHTML = `<div class="llm-msg-content" style="color: var(--error-text, #ef4444);">AI Assistant Error: ${this.escapeHTML(err.message)}</div>`;
    } finally {
      if (sendBtn) sendBtn.disabled = false;
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }

  handleLLMChipAction(action) {
    if (action === "explain-code") {
      let activeCode = "";
      if (this.editor && this.editor.notebook) {
        const blocks = this.editor.notebook.blocks || [];
        const codeBlock = blocks.find(b => b.type === "code");
        if (codeBlock) activeCode = codeBlock.content;
      }
      const prompt = activeCode
        ? `Please explain this code block line-by-line and identify any edge cases:\n\`\`\`python\n${activeCode}\n\`\`\``
        : "Explain how to write clean, maintainable Python code with unit tests.";
      this.sendLLMChatMessage(prompt);
    } else if (action === "summarize-notebook") {
      const title = this.editor && this.editor.notebook ? this.editor.notebook.title : "Workspace";
      this.sendLLMChatMessage(`Summarize the concepts and code in notebook "${title}" into structured study notes with bullet points.`);
    } else if (action === "summarize-reader") {
      const pageTitle = this.currentBrowserItem ? this.currentBrowserItem.title : "the active article";
      this.sendLLMChatMessage(`Provide a concise technical summary and key insights from ${pageTitle}.`);
    } else if (action === "fix-bug") {
      let activeCode = "";
      if (this.editor && this.editor.notebook) {
        const blocks = this.editor.notebook.blocks || [];
        const codeBlock = blocks.find(b => b.type === "code");
        if (codeBlock) activeCode = codeBlock.content;
      }
      this.sendLLMChatMessage(`Review this code for bugs, logic errors, or performance bottlenecks, and provide an optimized fix:\n\`\`\`python\n${activeCode || '# paste code here'}\n\`\`\``);
    } else if (action === "generate-python") {
      const input = this.panel.querySelector("#llm-prompt-input");
      if (input) {
        input.value = "Write a complete Python implementation for: ";
        input.focus();
      }
    }
  }

  formatLLMResponseHTML(text) {
    if (!text) return "";
    let html = this.escapeHTML(text);

    // Code blocks
    html = html.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      return `<pre style="margin: 8px 0; padding: 10px; background: var(--bg-tertiary); border-radius: var(--radius-sm); overflow-x: auto; font-family: var(--font-mono); font-size: 12px;"><code>${code}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, "<code style='background: var(--bg-tertiary); padding: 1px 4px; border-radius: 3px; font-family: var(--font-mono); font-size: 0.9em;'>$1</code>");

    // Headings
    html = html.replace(/^### (.*$)/gim, "<h4 style='margin: 8px 0 4px 0; font-size: 13.5px; font-weight: 700;'>$1</h4>");
    html = html.replace(/^## (.*$)/gim, "<h3 style='margin: 10px 0 4px 0; font-size: 14.5px; font-weight: 700;'>$1</h3>");
    html = html.replace(/^# (.*$)/gim, "<h2 style='margin: 12px 0 6px 0; font-size: 16px; font-weight: 800;'>$1</h2>");

    // Bold & italic
    html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");

    // Line breaks
    html = html.replace(/\n\n/g, "<p style='margin: 6px 0;'></p>");
    html = html.replace(/\n/g, "<br/>");

    return html;
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
