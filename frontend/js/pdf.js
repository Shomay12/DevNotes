/**
 * DevNote — PDF Export & Import Manager
 * Manages lossless PDF export and PDF notebook reconstruction.
 */

class PDFManager {
  constructor(appContext) {
    this.app = appContext;
    this.initExportModal();
    this.initImportModal();
  }

  initExportModal() {
    this.exportModal = document.getElementById("export-modal");
    if (!this.exportModal) return;

    this.btnConfirmExport = this.exportModal.querySelector(".btn-confirm-export");
    this.btnCloseExport = this.exportModal.querySelectorAll(".btn-close-modal");

    this.btnCloseExport.forEach(btn => {
      btn.addEventListener("click", () => this.closeExportModal());
    });

    if (this.btnConfirmExport) {
      this.btnConfirmExport.addEventListener("click", () => this.handleExport());
    }
  }

  initImportModal() {
    this.importModal = document.getElementById("import-modal");
    if (!this.importModal) return;

    this.fileInput = this.importModal.querySelector("#pdf-file-input");
    this.dropZone = this.importModal.querySelector(".pdf-drop-zone");
    this.btnUpload = this.importModal.querySelector(".btn-confirm-import");
    this.importTargetSelect = this.importModal.querySelector("#import-target-select");
    this.btnCloseImport = this.importModal.querySelectorAll(".btn-close-modal");

    this.btnCloseImport.forEach(btn => {
      btn.addEventListener("click", () => this.closeImportModal());
    });

    // File Drag & Drop
    if (this.dropZone) {
      ["dragenter", "dragover"].forEach(name => {
        this.dropZone.addEventListener(name, (e) => {
          e.preventDefault();
          this.dropZone.classList.add("dragover");
        });
      });

      ["dragleave", "drop"].forEach(name => {
        this.dropZone.addEventListener(name, (e) => {
          e.preventDefault();
          this.dropZone.classList.remove("dragover");
        });
      });

      this.dropZone.addEventListener("drop", (e) => {
        if (e.dataTransfer.files.length > 0) {
          this.fileInput.files = e.dataTransfer.files;
          this.updateSelectedFileLabel();
        }
      });

      this.dropZone.addEventListener("click", () => this.fileInput.click());
    }

    if (this.fileInput) {
      this.fileInput.addEventListener("change", () => this.updateSelectedFileLabel());
    }

    if (this.btnUpload) {
      this.btnUpload.addEventListener("click", () => this.handleImport());
    }
  }

  updateSelectedFileLabel() {
    const file = this.fileInput.files[0];
    const label = this.dropZone.querySelector(".drop-zone-text");
    if (file && label) {
      label.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      this.dropZone.style.borderColor = "var(--accent-primary)";
      this.dropZone.style.backgroundColor = "var(--accent-light)";
    }
  }

  openExportModal() {
    if (!this.app.currentNotebook) {
      this.app.showToast("No notebook is currently open to export.", "error");
      return;
    }
    this.exportModal.classList.add("open");
  }

  closeExportModal() {
    this.exportModal.classList.remove("open");
  }

  openImportModal() {
    if (this.importTargetSelect && this.app.currentNotebook) {
      this.importTargetSelect.innerHTML = `
        <option value="">Create as Canonical Notebook</option>
        <option value="${this.app.currentNotebook.id}">Append to current '${this.app.currentNotebook.title}'</option>
      `;
    }
    this.importModal.classList.add("open");
  }

  closeImportModal() {
    this.importModal.classList.remove("open");
    if (this.fileInput) this.fileInput.value = "";
    if (this.dropZone) {
      const label = this.dropZone.querySelector(".drop-zone-text");
      if (label) label.textContent = "Drag & drop DevNote PDF here or click to browse";
      this.dropZone.style.borderColor = "";
      this.dropZone.style.backgroundColor = "";
    }
  }

  async handleExport() {
    if (!this.app.currentNotebook) return;

    this.btnConfirmExport.disabled = true;
    this.btnConfirmExport.textContent = "Generating PDF...";

    try {
      // First ensure current notebook state is autosaved before export
      await this.app.editor.saveNow();

      const res = await API.exportPDF(this.app.currentNotebook.id);

      this.closeExportModal();
      this.app.showToast(`Exported ${res.filename} (${res.page_count} pages)`, "success");

      // Trigger automatic browser download
      const downloadLink = document.createElement("a");
      downloadLink.href = res.download_url;
      downloadLink.download = res.filename;
      downloadLink.target = "_blank";
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);

      // Refresh sidebar to reflect PDF export badge
      this.app.loadNotebookList();
    } catch (err) {
      this.app.showToast(`Export failed: ${err.message}`, "error");
    } finally {
      this.btnConfirmExport.disabled = false;
      this.btnConfirmExport.textContent = "Export & Download PDF";
    }
  }

  async handleImport() {
    const file = this.fileInput.files[0];
    if (!file) {
      this.app.showToast("Please select a PDF or JSON file to import.", "error");
      return;
    }

    this.btnUpload.disabled = true;
    this.btnUpload.textContent = "Importing & Reconstructing...";

    try {
      const formData = new FormData();
      formData.append("file", file);

      const targetId = this.importTargetSelect ? this.importTargetSelect.value : "";
      if (targetId) {
        formData.append("target_notebook_id", targetId);
      }

      let res;
      if (file.name.toLowerCase().endsWith(".json") || file.name.toLowerCase().endsWith(".devnote")) {
        res = await API.importJSON(formData);
        this.app.showToast(`Imported JSON notebook: '${res.title}'`, "success");
        this.closeImportModal();
        await this.app.loadNotebookList();
        await this.app.openNotebook(res.id);
      } else {
        res = await API.importPDF(formData);
        this.app.showToast(res.message, "success");
        this.closeImportModal();
        await this.app.loadNotebookList();
        await this.app.openNotebook(res.notebook_id);
      }
    } catch (err) {
      this.app.showToast(`Import failed: ${err.message}`, "error");
    } finally {
      this.btnUpload.disabled = false;
      this.btnUpload.textContent = "Upload & Reconstruct";
    }
  }
}

window.PDFManager = PDFManager;
