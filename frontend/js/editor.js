/**
 * DevNote — Main Notebook Document Editor
 * Block-based rich text, executable code, and stylus handwriting editor.
 */

class NotebookEditor {
  constructor(containerEl, appContext) {
    this.container = containerEl;
    this.app = appContext;

    this.notebook = null;
    this.blocks = [];
    this.blockComponents = new Map(); // blockId -> Component instance

    this.saveTimeout = null;
    this.isSaving = false;
    this.hasUnsavedChanges = false;
    this.activeBlockId = null;

    // Undo / Redo history
    this.historyStack = [];
    this.redoStack = [];

    this.initDOM();
    this.initSlashMenu();
    this.attachGlobalShortcuts();
  }

  initDOM() {
    this.container.innerHTML = `
      <div class="editor-top-bar">
        <div class="editor-title-container">
          <button type="button" class="btn btn-sidebar-toggle" id="btn-sidebar-toggle" title="Toggle Sidebar (Cmd+B)">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
          </button>
          <input type="text" class="notebook-title-input" placeholder="Untitled Notebook" value="" />
          <div class="save-status-indicator">
            <span class="save-status-text">Saved</span>
          </div>
        </div>
        <div class="editor-actions-group">
          <!-- Action Buttons -->
          <button type="button" class="btn btn-sm btn-toggle-search" title="Developer Search (Cmd+K)">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            Search
          </button>
          <button type="button" class="btn btn-sm btn-primary btn-open-export" title="Export PDF">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            Export PDF
          </button>
        </div>
      </div>
      <div class="editor-scroll-area">
        <div class="editor-document">
          <div class="document-meta-header">
            <div class="document-tags-bar">
              <div class="tags-list" style="display: flex; gap: 4px; align-items: center;"></div>
              <button type="button" class="btn-add-tag">+ Tag</button>
            </div>
            <div style="font-size: 11px; color: var(--text-muted);" class="doc-last-edited"></div>
          </div>
          <div class="document-blocks-container"></div>
        </div>
      </div>
      <!-- Slash Command Palette -->
      <div class="slash-command-palette">
        <div class="slash-palette-header">Insert Component</div>
        <div class="slash-item-list">
          <div class="slash-item" data-type="code" data-lang="python">
            <div class="slash-item-icon">PY</div>
            <div class="slash-item-details">
              <span class="slash-item-title">Python Code Block</span>
              <span class="slash-item-desc">Executable Python 3 with terminal output</span>
            </div>
          </div>
          <div class="slash-item" data-type="code" data-lang="javascript">
            <div class="slash-item-icon">JS</div>
            <div class="slash-item-details">
              <span class="slash-item-title">JavaScript Code Block</span>
              <span class="slash-item-desc">Executable Node.js script</span>
            </div>
          </div>
          <div class="slash-item" data-type="heading" data-level="1">
            <div class="slash-item-icon">H1</div>
            <div class="slash-item-details">
              <span class="slash-item-title">Heading 1</span>
              <span class="slash-item-desc">Large section header</span>
            </div>
          </div>
          <div class="slash-item" data-type="heading" data-level="2">
            <div class="slash-item-icon">H2</div>
            <div class="slash-item-details">
              <span class="slash-item-title">Heading 2</span>
              <span class="slash-item-desc">Medium subsection header</span>
            </div>
          </div>
          <div class="slash-item" data-type="drawing">
            <div class="slash-item-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
            </div>
            <div class="slash-item-details">
              <span class="slash-item-title">Handwritten Canvas</span>
              <span class="slash-item-desc">Stylus &amp; Pencil sketch block</span>
            </div>
          </div>
          <div class="slash-item" data-type="checklist">
            <div class="slash-item-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
            </div>
            <div class="slash-item-details">
              <span class="slash-item-title">Checklist</span>
              <span class="slash-item-desc">Interactive todo checkbox item</span>
            </div>
          </div>
          <div class="slash-item" data-type="math">
            <div class="slash-item-icon">∑</div>
            <div class="slash-item-details">
              <span class="slash-item-title">Math Formula</span>
              <span class="slash-item-desc">Formula and equation block</span>
            </div>
          </div>
          <div class="slash-item" data-type="table">
            <div class="slash-item-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
            </div>
            <div class="slash-item-details">
              <span class="slash-item-title">Table</span>
              <span class="slash-item-desc">Structured rows &amp; columns</span>
            </div>
          </div>
        </div>
      </div>
    `;

    this.titleInput = this.container.querySelector(".notebook-title-input");
    this.statusText = this.container.querySelector(".save-status-text");
    this.blocksContainer = this.container.querySelector(".document-blocks-container");
    this.tagsList = this.container.querySelector(".tags-list");
    this.btnAddTag = this.container.querySelector(".btn-add-tag");
    this.lastEditedLabel = this.container.querySelector(".doc-last-edited");
    this.slashPalette = this.container.querySelector(".slash-command-palette");

    // Sidebar Toggle
    const sidebarToggleBtn = this.container.querySelector("#btn-sidebar-toggle");
    if (sidebarToggleBtn) {
      sidebarToggleBtn.addEventListener("click", () => {
        if (this.app && typeof this.app.toggleSidebar === "function") {
          this.app.toggleSidebar();
        }
      });
    }

    // Title editing triggers debounced autosave
    this.titleInput.addEventListener("input", () => {
      if (this.notebook) {
        this.notebook.title = this.titleInput.value;
        this.scheduleAutosave();
      }
    });

    // Tag adding
    this.btnAddTag.addEventListener("click", () => {
      const tag = prompt("Enter tag name (e.g. 'algorithms', 'backend'):");
      if (tag && tag.trim()) {
        const cleanTag = tag.trim().toLowerCase();
        if (!this.notebook.tags) this.notebook.tags = [];
        if (!this.notebook.tags.includes(cleanTag)) {
          this.notebook.tags.push(cleanTag);
          this.renderTags();
          this.scheduleAutosave();
        }
      }
    });

    // Header Action Buttons
    const searchToggleBtn = this.container.querySelector(".btn-toggle-search");
    if (searchToggleBtn) {
      searchToggleBtn.addEventListener("click", () => {
        this.app.searchWorkspace.toggleCollapse();
      });
    }

    const snippetsBtn = this.container.querySelector(".btn-snippets-modal");
    if (snippetsBtn) {
      snippetsBtn.addEventListener("click", () => {
        this.app.openSnippetsModal();
      });
    }

    const exportJsonBtn = this.container.querySelector(".btn-export-json");
    if (exportJsonBtn) {
      exportJsonBtn.addEventListener("click", () => {
        this.app.exportCurrentNotebookJSON();
      });
    }

    const openExportBtn = this.container.querySelector(".btn-open-export");
    if (openExportBtn) {
      openExportBtn.addEventListener("click", () => {
        this.app.pdfManager.openExportModal();
      });
    }

    // View Mode Filters (if present)
    const modeBtns = this.container.querySelectorAll(".btn-mode-toggle");
    modeBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        modeBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.filterBlocksByMode(btn.dataset.mode);
      });
    });
  }

  filterBlocksByMode(mode) {
    const blocks = this.blocksContainer.querySelectorAll(".notebook-block");
    blocks.forEach(b => {
      const type = b.dataset.blockType;
      if (mode === "all") {
        b.style.display = "block";
      } else if (mode === "code") {
        b.style.display = type === "code" ? "block" : "none";
      } else if (mode === "drawing") {
        b.style.display = type === "drawing" ? "block" : "none";
      }
    });
  }

  initSlashMenu() {
    const items = this.slashPalette.querySelectorAll(".slash-item");
    items.forEach(item => {
      item.addEventListener("click", () => {
        const type = item.dataset.type;
        const lang = item.dataset.lang;
        const level = parseInt(item.dataset.level) || 2;
        this.insertBlockFromSlash(type, { language: lang, level });
      });
    });

    // Close slash menu on outside click
    document.addEventListener("click", (e) => {
      if (!this.slashPalette.contains(e.target)) {
        this.closeSlashMenu();
      }
    });
  }

  attachGlobalShortcuts() {
    window.addEventListener("keydown", (e) => {
      // Cmd/Ctrl + S -> Save Immediately
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        this.saveNow();
      }
      // Cmd/Ctrl + K -> Toggle Developer Search
      else if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        this.app.searchWorkspace.toggleCollapse();
      }
      // Cmd/Ctrl + B or \ -> Toggle Left Sidebar
      else if ((e.metaKey || e.ctrlKey) && (e.key === "b" || e.key === "B" || e.key === "\\")) {
        e.preventDefault();
        if (this.app && typeof this.app.toggleSidebar === "function") {
          this.app.toggleSidebar();
        }
      }
    });
  }

  loadNotebook(notebook) {
    this.notebook = notebook;
    this.titleInput.value = notebook.title || "Untitled Notebook";
    this.blocks = notebook.blocks ? JSON.parse(JSON.stringify(notebook.blocks)) : [];
    this.blockComponents.clear();

    this.renderTags();
    this.renderBlocks();
    this.updateLastEditedText();
    this.setStatus("saved");
  }

  renderTags() {
    this.tagsList.innerHTML = "";
    const tags = this.notebook.tags || [];
    tags.forEach(t => {
      const span = document.createElement("span");
      span.className = "tag-badge";
      span.innerHTML = `#${this.escapeHTML(t)} <span style="cursor: pointer; margin-left: 2px;">×</span>`;
      span.querySelector("span").addEventListener("click", () => {
        this.notebook.tags = this.notebook.tags.filter(item => item !== t);
        this.renderTags();
        this.scheduleAutosave();
      });
      this.tagsList.appendChild(span);
    });
  }

  updateLastEditedText() {
    if (this.notebook.last_edited_at) {
      try {
        const d = new Date(this.notebook.last_edited_at);
        this.lastEditedLabel.textContent = `Last edited: ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      } catch (_) {
        this.lastEditedLabel.textContent = "";
      }
    }
  }

  renderBlocks() {
    this.blocksContainer.innerHTML = "";

    if (this.blocks.length === 0) {
      // Provide an empty starting paragraph block
      this.blocks.push({
        id: `block-${this.generateUUID()}`,
        type: "paragraph",
        content: ""
      });
    }

    this.blocks.forEach((block, index) => {
      // 1. Divider line with "+" to insert block between
      const divider = this.createAddDivider(index);
      this.blocksContainer.appendChild(divider);

      // 2. Block Element
      const blockEl = this.renderSingleBlock(block, index);
      this.blocksContainer.appendChild(blockEl);
    });

    // Final bottom divider
    const bottomDivider = this.createAddDivider(this.blocks.length);
    this.blocksContainer.appendChild(bottomDivider);
  }

  createAddDivider(index) {
    const div = document.createElement("div");
    div.className = "add-block-divider";
    div.innerHTML = `
      <div class="add-block-line"></div>
      <button type="button" class="add-block-plus-btn" title="Insert component here">+</button>
    `;

    const plusBtn = div.querySelector(".add-block-plus-btn");
    plusBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this.openSlashMenu(e.clientX, e.clientY, index);
    });

    return div;
  }

  renderSingleBlock(block, index) {
    const blockEl = document.createElement("div");
    blockEl.className = "notebook-block";
    blockEl.dataset.blockId = block.id;
    blockEl.dataset.blockType = block.type;

    // Hover Controls: Move Up, Move Down, Duplicate, Delete
    const controls = document.createElement("div");
    controls.className = "block-hover-controls";
    controls.innerHTML = `
      <button type="button" class="block-action-btn" title="Move Up" data-action="up">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="18 15 12 9 6 15"></polyline></svg>
      </button>
      <button type="button" class="block-action-btn" title="Move Down" data-action="down">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"></polyline></svg>
      </button>
      <button type="button" class="block-action-btn" title="Duplicate Block" data-action="duplicate">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
      </button>
      <button type="button" class="block-action-btn delete-btn" title="Delete Block" data-action="delete">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
      </button>
    `;

    controls.querySelector('[data-action="up"]').addEventListener("click", () => this.moveBlock(index, -1));
    controls.querySelector('[data-action="down"]').addEventListener("click", () => this.moveBlock(index, 1));
    controls.querySelector('[data-action="duplicate"]').addEventListener("click", () => this.duplicateBlock(index));
    controls.querySelector('[data-action="delete"]').addEventListener("click", () => this.deleteBlock(index));

    blockEl.appendChild(controls);

    // Render by type
    if (block.type === "heading") {
      const heading = document.createElement("div");
      heading.className = `block-heading level-${block.level || 2}`;
      heading.contentEditable = "true";
      heading.textContent = block.content || "";
      heading.addEventListener("input", () => {
        block.content = heading.textContent;
        this.scheduleAutosave();
      });
      blockEl.appendChild(heading);

    } else if (block.type === "paragraph") {
      const p = document.createElement("div");
      p.className = "block-paragraph";
      p.contentEditable = "true";
      p.textContent = block.content || "";

      p.addEventListener("input", () => {
        block.content = p.textContent;
        // Check if slash command was typed
        if (p.textContent === "/") {
          const rect = p.getBoundingClientRect();
          this.openSlashMenu(rect.left, rect.bottom + 5, index);
        }
        this.scheduleAutosave();
      });

      // Enter key creates next paragraph block
      p.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          this.insertBlockAtIndex(index + 1, {
            id: `block-${this.generateUUID()}`,
            type: "paragraph",
            content: ""
          });
        }
      });

      blockEl.appendChild(p);

    } else if (block.type === "code") {
      const codeComponent = new CodeBlockComponent(
        block,
        this.notebook ? this.notebook.id : null,
        (updatedData) => {
          Object.assign(block, updatedData);
          this.scheduleAutosave();
        }
      );
      this.blockComponents.set(block.id, codeComponent);
      blockEl.appendChild(codeComponent.element);

    } else if (block.type === "drawing") {
      const canvasContainer = document.createElement("div");
      blockEl.appendChild(canvasContainer);

      setTimeout(() => {
        const hwCanvas = new HandwritingCanvas(
          canvasContainer,
          block,
          (updatedDrawing) => {
            block.strokes = updatedDrawing.strokes;
            block.image_data = updatedDrawing.image_data;
            this.scheduleAutosave();
          }
        );
        this.blockComponents.set(block.id, hwCanvas);
      }, 0);

    } else if (block.type === "checklist") {
      const checkContainer = document.createElement("div");
      checkContainer.className = "block-checklist";
      checkContainer.innerHTML = `
        <input type="checkbox" class="checklist-checkbox" ${block.checked ? "checked" : ""} />
        <div class="checklist-text ${block.checked ? "checked" : ""}" contenteditable="true">${this.escapeHTML(block.content || "")}</div>
      `;

      const cb = checkContainer.querySelector(".checklist-checkbox");
      const txt = checkContainer.querySelector(".checklist-text");

      cb.addEventListener("change", () => {
        block.checked = cb.checked;
        txt.classList.toggle("checked", cb.checked);
        this.scheduleAutosave();
      });

      txt.addEventListener("input", () => {
        block.content = txt.textContent;
        this.scheduleAutosave();
      });

      blockEl.appendChild(checkContainer);

    } else if (block.type === "math") {
      const mathContainer = document.createElement("div");
      mathContainer.className = "math-block-container";
      mathContainer.innerHTML = `
        <div style="font-weight: 600; font-size: 11px; text-transform: uppercase; color: var(--text-muted);">Math Formula:</div>
        <input type="text" class="form-input" style="flex: 1; font-family: var(--font-mono); margin: 0 10px;" value="${this.escapeHTML(block.content || block.expression || 'E = mc^2')}" />
      `;
      const input = mathContainer.querySelector("input");
      input.addEventListener("input", () => {
        block.content = input.value;
        block.expression = input.value;
        this.scheduleAutosave();
      });
      blockEl.appendChild(mathContainer);

    } else if (block.type === "table") {
      const tableContainer = document.createElement("div");
      tableContainer.className = "table-block-container";
      const rows = block.rows || [
        ["Concept", "Description", "Complexity"],
        ["Hash Map", "Key-value pair store", "O(1) avg"],
        ["Binary Tree", "Hierarchical structure", "O(log n)"]
      ];
      block.rows = rows;

      let tableHTML = `<table class="devnote-table"><tbody>`;
      rows.forEach((row, rIdx) => {
        tableHTML += `<tr>`;
        row.forEach((cell, cIdx) => {
          const tag = rIdx === 0 ? "th" : "td";
          tableHTML += `<${tag} contenteditable="true" data-row="${rIdx}" data-col="${cIdx}">${this.escapeHTML(cell)}</${tag}>`;
        });
        tableHTML += `</tr>`;
      });
      tableHTML += `</tbody></table>`;
      tableContainer.innerHTML = tableHTML;

      tableContainer.querySelectorAll("[contenteditable]").forEach(cell => {
        cell.addEventListener("input", () => {
          const r = parseInt(cell.dataset.row);
          const c = parseInt(cell.dataset.col);
          block.rows[r][c] = cell.textContent;
          this.scheduleAutosave();
        });
      });

      blockEl.appendChild(tableContainer);
    }

    return blockEl;
  }

  openSlashMenu(x, y, insertIndex) {
    this.slashInsertIndex = insertIndex;
    this.slashPalette.style.left = `${Math.min(x, window.innerWidth - 300)}px`;
    this.slashPalette.style.top = `${Math.min(y, window.innerHeight - 320)}px`;
    this.slashPalette.classList.add("open");
  }

  closeSlashMenu() {
    this.slashPalette.classList.remove("open");
  }

  insertBlockFromSlash(type, options = {}) {
    this.closeSlashMenu();
    const index = this.slashInsertIndex !== undefined ? this.slashInsertIndex : this.blocks.length;

    const newBlock = {
      id: `block-${this.generateUUID()}`,
      type,
    };

    if (type === "code") {
      newBlock.language = options.language || "python";
      newBlock.code = options.language === "javascript" ? "console.log('Hello from JavaScript!');" : "print('Hello from Python!')";
      newBlock.output = "";
      newBlock.error = "";
      newBlock.status = "idle";
    } else if (type === "heading") {
      newBlock.level = options.level || 2;
      newBlock.content = "New Section Header";
    } else if (type === "drawing") {
      newBlock.strokes = [];
      newBlock.image_data = null;
    } else if (type === "checklist") {
      newBlock.checked = false;
      newBlock.content = "Task item";
    } else if (type === "math") {
      newBlock.content = "f(x) = \\int_{0}^{\\infty} e^{-x} dx";
    } else if (type === "table") {
      newBlock.rows = [
        ["Key", "Value"],
        ["Param 1", "Active"],
        ["Param 2", "Standby"]
      ];
    } else {
      newBlock.content = "";
    }

    this.insertBlockAtIndex(index, newBlock);
  }

  insertBlockAtIndex(index, block) {
    this.blocks.splice(index, 0, block);
    this.renderBlocks();
    this.scheduleAutosave();

    // Focus newly created element
    setTimeout(() => {
      const el = this.blocksContainer.querySelector(`[data-block-id="${block.id}"]`);
      if (el) {
        const editable = el.querySelector('[contenteditable="true"], textarea');
        if (editable) editable.focus();
      }
    }, 50);
  }

  moveBlock(index, offset) {
    const newIndex = index + offset;
    if (newIndex < 0 || newIndex >= this.blocks.length) return;

    const [moved] = this.blocks.splice(index, 1);
    this.blocks.splice(newIndex, 0, moved);
    this.renderBlocks();
    this.scheduleAutosave();
  }

  duplicateBlock(index) {
    const original = this.blocks[index];
    const clone = JSON.parse(JSON.stringify(original));
    clone.id = `block-${this.generateUUID()}`;
    this.insertBlockAtIndex(index + 1, clone);
  }

  deleteBlock(index) {
    this.blocks.splice(index, 1);
    this.renderBlocks();
    this.scheduleAutosave();
  }

  /**
   * Insert Search Result Item directly into current notebook
   * Never overwrites existing blocks! Supports insertion modes: 'both', 'reference', 'code', 'evidence'.
   */
  insertSearchResult(searchItem, mode = "both") {
    if (!this.notebook) return;

    const today = new Date().toISOString().slice(0, 10);

    // 1. Insert Evidence Quote Block
    if (mode === "evidence") {
      const quoteText = searchItem.evidence || searchItem.quote || searchItem.snippet || "";
      const noteText = searchItem.note || searchItem.explanation || "";
      const sourceTitle = searchItem.title || "Research Source";
      const sourceUrl = searchItem.url || "";

      let blockContent = "";
      if (quoteText) {
        const quotedLines = quoteText.split("\n").map(l => `> ${l}`).join("\n");
        blockContent += `${quotedLines}\n>\n`;
      }
      blockContent += `> **Source:** ${sourceUrl ? `[${sourceTitle}](${sourceUrl})` : sourceTitle}\n`;
      blockContent += `> **Retrieved:** ${today}`;
      if (noteText) {
        blockContent += `\n>\n> **Note:** ${noteText}`;
      }

      const evidenceBlock = {
        id: `block-${this.generateUUID()}`,
        type: "paragraph",
        content: blockContent.trim(),
      };
      this.blocks.push(evidenceBlock);
    }
    // 2. Insert Standard Reference (Heading + Description + Source Link)
    else if (mode === "both" || mode === "reference") {
      const titleBlock = {
        id: `block-${this.generateUUID()}`,
        type: "heading",
        level: 2,
        content: searchItem.title,
      };
      this.blocks.push(titleBlock);

      let refContent = searchItem.snippet || "";
      if (searchItem.url) {
        refContent += `\n\nSource: ${searchItem.source || "DevSearch"} (${searchItem.url})\nRetrieved: ${today}`;
      }
      if (searchItem.note) {
        refContent += `\n\nPersonal Note: ${searchItem.note}`;
      }
      const snipBlock = {
        id: `block-${this.generateUUID()}`,
        type: "paragraph",
        content: refContent,
      };
      this.blocks.push(snipBlock);
    }

    // 3. Insert Executable Code Block
    if ((mode === "both" || mode === "code") && searchItem.code) {
      const codeBlock = {
        id: `block-${this.generateUUID()}`,
        type: "code",
        language: searchItem.language || "python",
        code: searchItem.code,
        output: "",
        error: "",
        status: "idle",
      };
      this.blocks.push(codeBlock);
    }

    this.renderBlocks();
    this.scheduleAutosave();
    const actionLabel = mode === "code" ? "code block" : mode === "reference" ? "reference" : mode === "evidence" ? "evidence citation" : "content";
    this.app.showToast(`Inserted ${actionLabel} from "${searchItem.title}"`, "success");

    // Scroll to bottom
    const scrollArea = this.container.querySelector(".editor-scroll-area");
    if (scrollArea) {
      setTimeout(() => {
        scrollArea.scrollTop = scrollArea.scrollHeight;
      }, 50);
    }
  }

  // Autosave Management
  scheduleAutosave() {
    this.setStatus("unsaved");
    this.hasUnsavedChanges = true;

    clearTimeout(this.saveTimeout);
    this.saveTimeout = setTimeout(() => {
      this.saveNow();
    }, 800); // 800ms debounce
  }

  async saveNow() {
    if (!this.notebook) return;

    clearTimeout(this.saveTimeout);
    this.setStatus("saving");

    try {
      // Gather latest state from active components
      this.blockComponents.forEach((comp, id) => {
        if (typeof comp.getData === "function") {
          const b = this.blocks.find(x => x.id === id);
          if (b) Object.assign(b, comp.getData());
        }
      });

      const updated = await API.autosaveContent(this.notebook.id, {
        blocks: this.blocks,
        title: this.titleInput.value || this.notebook.title,
        tags: this.notebook.tags,
      });

      this.notebook.version = updated.version;
      this.notebook.last_edited_at = updated.last_edited_at;
      this.hasUnsavedChanges = false;
      this.setStatus("saved");
      this.updateLastEditedText();

      // Refresh sidebar list title
      this.app.updateSidebarNotebookTitle(this.notebook.id, this.titleInput.value);
    } catch (err) {
      console.error("Autosave error:", err);
      this.setStatus("error");
    }
  }

  setStatus(status) {
    if (!this.statusText) return;
    if (status === "saving") {
      this.statusText.textContent = "Saving...";
      this.statusText.className = "save-status-text saving";
    } else if (status === "saved") {
      this.statusText.textContent = "Saved";
      this.statusText.className = "save-status-text saved";
    } else if (status === "unsaved") {
      this.statusText.textContent = "Unsaved";
      this.statusText.className = "save-status-text unsaved";
    } else if (status === "error") {
      this.statusText.textContent = "Save error";
      this.statusText.className = "save-status-text error";
    }
  }

  generateUUID() {
    return Math.random().toString(36).substring(2, 10);
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

window.NotebookEditor = NotebookEditor;
