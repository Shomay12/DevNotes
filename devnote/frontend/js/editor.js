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
          <input type="text" class="notebook-title-input" placeholder="Untitled Notebook" value="" />
          <div class="save-status-indicator">
            <span class="status-dot"></span>
            <span class="save-status-text">All changes saved</span>
          </div>
        </div>
        <div class="editor-actions-group">
          <!-- View Modes -->
          <button type="button" class="btn btn-sm btn-mode-toggle active" data-mode="all" title="All Blocks">All</button>
          <button type="button" class="btn btn-sm btn-mode-toggle" data-mode="code" title="Code Only">Code</button>
          <button type="button" class="btn btn-sm btn-mode-toggle" data-mode="drawing" title="Handwriting">Draw</button>
          <div style="width: 1px; height: 18px; background: var(--border-subtle); margin: 0 4px;"></div>
          <!-- Action Buttons -->
          <button type="button" class="btn btn-sm btn-toggle-search" title="Developer Search (Cmd+K)">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            Search
          </button>
          <button type="button" class="btn btn-sm btn-snippets-modal" title="Insert Snippet">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
            Snippets
          </button>
          <button type="button" class="btn btn-sm btn-export-json" title="Export Canonical JSON Notebook">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            JSON
          </button>
          <button type="button" class="btn btn-sm btn-primary btn-open-export" title="Export as PDF">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            Export PDF
          </button>
        </div>
      </div>
      <div class="editor-scroll-area">
        <div class="editor-document">
          <div class="document-meta-header">
            <div class="document-tags-bar">
              <span style="font-size: 11px; font-weight: 600; color: var(--text-muted);">Tags:</span>
              <div class="tags-list" style="display: flex; gap: 4px; align-items: center;"></div>
              <button type="button" class="btn-add-tag">+ Add Tag</button>
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
            <div class="slash-item-icon">py</div>
            <div class="slash-item-details">
              <span class="slash-item-title">Python Code Block</span>
              <span class="slash-item-desc">Executable Python 3 with terminal output</span>
            </div>
          </div>
          <div class="slash-item" data-type="code" data-lang="javascript">
            <div class="slash-item-icon">js</div>
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
            <div class="slash-item-icon">✎</div>
            <div class="slash-item-details">
              <span class="slash-item-title">Handwritten Canvas</span>
              <span class="slash-item-desc">Apple Pencil and stylus drawing canvas</span>
            </div>
          </div>
          <div class="slash-item" data-type="checklist">
            <div class="slash-item-icon">☑</div>
            <div class="slash-item-details">
              <span class="slash-item-title">Checklist</span>
              <span class="slash-item-desc">Interactive todo checkbox item</span>
            </div>
          </div>
          <div class="slash-item" data-type="math">
            <div class="slash-item-icon">∑</div>
            <div class="slash-item-details">
              <span class="slash-item-title">Math Equation</span>
              <span class="slash-item-desc">Mathematical formula block</span>
            </div>
          </div>
          <div class="slash-item" data-type="table">
            <div class="slash-item-icon">⊞</div>
            <div class="slash-item-details">
              <span class="slash-item-title">Table</span>
              <span class="slash-item-desc">Data table with rows & columns</span>
            </div>
          </div>
        </div>
      </div>
    `;

    this.titleInput = this.container.querySelector(".notebook-title-input");
    this.statusDot = this.container.querySelector(".status-dot");
    this.statusText = this.container.querySelector(".save-status-text");
    this.blocksContainer = this.container.querySelector(".document-blocks-container");
    this.tagsList = this.container.querySelector(".tags-list");
    this.btnAddTag = this.container.querySelector(".btn-add-tag");
    this.lastEditedLabel = this.container.querySelector(".doc-last-edited");
    this.slashPalette = this.container.querySelector(".slash-command-palette");

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
    this.container.querySelector(".btn-toggle-search").addEventListener("click", () => {
      this.app.searchWorkspace.toggleCollapse();
    });

    this.container.querySelector(".btn-snippets-modal").addEventListener("click", () => {
      this.app.openSnippetsModal();
    });

    this.container.querySelector(".btn-export-json").addEventListener("click", () => {
      this.app.exportCurrentNotebookJSON();
    });

    this.container.querySelector(".btn-open-export").addEventListener("click", () => {
      this.app.pdfManager.openExportModal();
    });

    // View Mode Filters
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
      <button type="button" class="block-action-btn" title="Move Up" data-action="up">↑</button>
      <button type="button" class="block-action-btn" title="Move Down" data-action="down">↓</button>
      <button type="button" class="block-action-btn" title="Duplicate Block" data-action="duplicate">❐</button>
      <button type="button" class="block-action-btn delete-btn" title="Delete Block" data-action="delete">✕</button>
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
   * Never overwrites existing blocks! Supports insertion modes: 'both', 'reference', 'code'.
   */
  insertSearchResult(searchItem, mode = "both") {
    if (!this.notebook) return;

    // 1. Insert Reference (Heading + Description + Source Link)
    if (mode === "both" || mode === "reference") {
      const titleBlock = {
        id: `block-${this.generateUUID()}`,
        type: "heading",
        level: 2,
        content: searchItem.title,
      };
      this.blocks.push(titleBlock);

      let refContent = searchItem.snippet || "";
      if (searchItem.url) {
        refContent += `\n\nSource: ${searchItem.source || "DevSearch"} (${searchItem.url})`;
      }
      const snipBlock = {
        id: `block-${this.generateUUID()}`,
        type: "paragraph",
        content: refContent,
      };
      this.blocks.push(snipBlock);
    }

    // 2. Insert Executable Code Block
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
    const actionLabel = mode === "code" ? "code block" : mode === "reference" ? "reference" : "content";
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
    if (status === "saving") {
      this.statusDot.className = "status-dot saving";
      this.statusText.textContent = "Saving...";
    } else if (status === "saved") {
      this.statusDot.className = "status-dot";
      this.statusText.textContent = "All changes saved";
    } else if (status === "unsaved") {
      this.statusDot.className = "status-dot unsaved";
      this.statusText.textContent = "Unsaved changes";
    } else if (status === "error") {
      this.statusDot.className = "status-dot unsaved";
      this.statusText.textContent = "Error saving";
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
