/**
 * DevNote — Executable Code Block Component
 * Manages Python & JavaScript isolated execution, line numbering,
 * stdout/stderr terminal display, and execution history.
 */

class CodeBlockComponent {
  constructor(blockData, notebookId, onBlockChange) {
    this.data = {
      id: blockData.id,
      language: blockData.language || "python",
      code: blockData.code || "",
      output: blockData.output || "",
      error: blockData.error || "",
      status: blockData.status || "idle",
      execution_time_ms: blockData.execution_time_ms || 0.0,
      history: blockData.history || [],
    };
    this.notebookId = notebookId;
    this.onBlockChange = onBlockChange;
    this.activeExecutionId = null;

    this.element = this.createDOM();
    this.attachEvents();
    this.updateLineNumbers();
  }

  createDOM() {
    const div = document.createElement("div");
    div.className = "code-block-container";
    div.dataset.blockId = this.data.id;

    const isRunning = this.data.status === "running";
    const statusText = isRunning
      ? "Running..."
      : this.data.status === "success"
      ? `Done (${this.data.execution_time_ms}ms)`
      : this.data.status === "error"
      ? "Failed"
      : this.data.status === "timeout"
      ? "Timeout"
      : "Idle";

    const statusClass = this.data.status || "idle";

    div.innerHTML = `
      <div class="code-block-header">
        <div class="code-header-left">
          <select class="lang-selector" title="Choose Language">
            <option value="python" ${this.data.language === "python" ? "selected" : ""}>Python 3</option>
            <option value="javascript" ${this.data.language === "javascript" ? "selected" : ""}>JavaScript</option>
          </select>
          <div class="code-status-pill ${statusClass}">
            <span class="status-dot ${isRunning ? "saving" : ""}"></span>
            <span class="status-label">${statusText}</span>
          </div>
        </div>
        <div class="code-header-right">
          <button type="button" class="btn btn-sm btn-clear-output" title="Clear Output" ${!this.data.output && !this.data.error ? "disabled" : ""}>
            Clear
          </button>
          <button type="button" class="btn btn-sm btn-stop-code" style="display: ${isRunning ? "inline-flex" : "none"}; color: var(--error-text);" title="Stop Process">
            Stop
          </button>
          <button type="button" class="btn btn-sm btn-primary btn-run-code" title="Execute (Cmd/Ctrl + Enter)">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            Run
          </button>
        </div>
      </div>
      <div class="code-editor-wrapper">
        <div class="code-line-numbers">1</div>
        <textarea class="code-textarea" spellcheck="false" placeholder="Write code here...">${this.escapeHTML(this.data.code)}</textarea>
      </div>
      <div class="code-output-container" style="display: ${this.data.output ? "block" : "none"}">
        <div class="code-output-header">
          <span>Output</span>
          <span style="font-size: 10px; color: #94a3b8;">${this.data.execution_time_ms ? `${this.data.execution_time_ms}ms` : ""}</span>
        </div>
        <div class="code-output-content">${this.escapeHTML(this.data.output)}</div>
      </div>
      <div class="code-error-container" style="display: ${this.data.error ? "block" : "none"}">${this.escapeHTML(this.data.error)}</div>
    `;

    return div;
  }

  attachEvents() {
    this.textarea = this.element.querySelector(".code-textarea");
    this.langSelect = this.element.querySelector(".lang-selector");
    this.runBtn = this.element.querySelector(".btn-run-code");
    this.stopBtn = this.element.querySelector(".btn-stop-code");
    this.clearBtn = this.element.querySelector(".btn-clear-output");
    this.statusPill = this.element.querySelector(".code-status-pill");
    this.statusLabel = this.element.querySelector(".status-label");
    this.statusDot = this.element.querySelector(".status-dot");
    this.outputContainer = this.element.querySelector(".code-output-container");
    this.outputContent = this.element.querySelector(".code-output-content");
    this.errorContainer = this.element.querySelector(".code-error-container");
    this.lineNumbers = this.element.querySelector(".code-line-numbers");

    // Textarea input & line number sync
    this.textarea.addEventListener("input", () => {
      this.data.code = this.textarea.value;
      this.updateLineNumbers();
      this.autoResize();
      this.notifyChange();
    });

    // Smart Tab indentation (4 spaces) & Cmd+Enter execution
    this.textarea.addEventListener("keydown", (e) => {
      if (e.key === "Tab") {
        e.preventDefault();
        const start = this.textarea.selectionStart;
        const end = this.textarea.selectionEnd;
        const spaces = "    ";
        this.textarea.value = this.textarea.value.substring(0, start) + spaces + this.textarea.value.substring(end);
        this.textarea.selectionStart = this.textarea.selectionEnd = start + 4;
        this.data.code = this.textarea.value;
        this.updateLineNumbers();
        this.notifyChange();
      } else if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        this.run();
      }
    });

    // Language change
    this.langSelect.addEventListener("change", (e) => {
      this.data.language = e.target.value;
      this.notifyChange();
    });

    // Run action
    this.runBtn.addEventListener("click", () => this.run());

    // Stop action
    this.stopBtn.addEventListener("click", () => this.stop());

    // Clear output
    this.clearBtn.addEventListener("click", () => this.clearOutput());

    // Auto resize initial height
    setTimeout(() => this.autoResize(), 50);
  }

  updateLineNumbers() {
    const lines = (this.textarea.value || "").split("\n").length;
    const nums = Array.from({ length: Math.max(lines, 1) }, (_, i) => i + 1).join("<br>");
    this.lineNumbers.innerHTML = nums;
  }

  autoResize() {
    this.textarea.style.height = "auto";
    const newHeight = Math.max(this.textarea.scrollHeight, 60);
    this.textarea.style.height = `${newHeight}px`;
    this.lineNumbers.style.height = `${newHeight}px`;
  }

  setStatus(status, message = null) {
    this.data.status = status;
    this.statusPill.className = `code-status-pill ${status}`;
    this.statusDot.className = `status-dot ${status === "running" ? "saving" : ""}`;

    if (message) {
      this.statusLabel.textContent = message;
    } else if (status === "running") {
      this.statusLabel.textContent = "Running...";
    } else if (status === "success") {
      this.statusLabel.textContent = `Done (${this.data.execution_time_ms}ms)`;
    } else if (status === "error") {
      this.statusLabel.textContent = "Failed";
    } else if (status === "timeout") {
      this.statusLabel.textContent = "Timeout";
    } else {
      this.statusLabel.textContent = "Idle";
    }

    this.runBtn.disabled = status === "running";
    this.stopBtn.style.display = status === "running" ? "inline-flex" : "none";
  }

  async run() {
    const code = this.textarea.value.trim();
    if (!code) return;

    this.setStatus("running");

    try {
      const res = await API.executeCode({
        language: this.data.language,
        code: this.textarea.value,
        notebookId: this.notebookId,
        blockId: this.data.id,
      });

      this.activeExecutionId = res.execution_id;
      this.data.output = res.output || "";
      this.data.error = res.error || "";
      this.data.execution_time_ms = res.execution_time_ms || 0.0;
      this.data.status = res.status;

      // Update UI Output
      if (this.data.output) {
        this.outputContainer.style.display = "block";
        this.outputContent.textContent = this.data.output;
      } else {
        this.outputContainer.style.display = "none";
      }

      // Update UI Error
      if (this.data.error) {
        this.errorContainer.style.display = "block";
        this.errorContainer.textContent = this.data.error;
      } else {
        this.errorContainer.style.display = "none";
      }

      this.clearBtn.disabled = !this.data.output && !this.data.error;
      this.setStatus(res.status);
      this.notifyChange();
    } catch (err) {
      this.data.status = "error";
      this.data.error = err.message || "Execution failed";
      this.errorContainer.style.display = "block";
      this.errorContainer.textContent = this.data.error;
      this.setStatus("error", "Error");
      this.notifyChange();
    }
  }

  async stop() {
    if (this.activeExecutionId) {
      try {
        await API.stopExecution(this.activeExecutionId);
        this.setStatus("idle", "Stopped");
      } catch (_) {}
    }
  }

  clearOutput() {
    this.data.output = "";
    this.data.error = "";
    this.outputContainer.style.display = "none";
    this.errorContainer.style.display = "none";
    this.clearBtn.disabled = true;
    this.setStatus("idle");
    this.notifyChange();
  }

  notifyChange() {
    if (typeof this.onBlockChange === "function") {
      this.onBlockChange(this.getData());
    }
  }

  getData() {
    return {
      ...this.data,
      code: this.textarea.value,
    };
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

window.CodeBlockComponent = CodeBlockComponent;
