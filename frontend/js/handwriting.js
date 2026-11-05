/**
 * DevNote — Handwriting & Apple Pencil Drawing Engine
 * Powered by HTML5 Canvas & Pointer Events API with Pressure Sensitivity
 */

class HandwritingCanvas {
  constructor(containerEl, initialData = {}, onUpdate = null) {
    this.container = containerEl;
    this.onUpdate = onUpdate;

    this.strokes = initialData.strokes ? [...initialData.strokes] : [];
    this.redoStack = [];
    this.currentStroke = null;

    // Default Tool Settings
    this.tool = "pen"; // 'pen', 'highlighter', 'eraser'
    this.color = "#2563eb"; // default royal blue
    this.lineWidth = 2.5;

    this.initDOM();
    this.initCanvas();
    this.attachEvents();

    if (initialData.image_data) {
      this.loadImage(initialData.image_data);
    } else if (this.strokes.length > 0) {
      this.redrawAll();
    }
  }

  initDOM() {
    this.container.innerHTML = `
      <div class="drawing-block-container">
        <div class="drawing-toolbar">
          <div class="drawing-tools-left">
            <button type="button" class="draw-tool-btn active" data-tool="pen" title="Pen (Apple Pencil)">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
            </button>
            <button type="button" class="draw-tool-btn" data-tool="highlighter" title="Highlighter">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 11-6 6v3h3l6-6m-6 3 3 3m7-14 3 3L7 19l-3-3L17 3z"></path></svg>
            </button>
            <button type="button" class="draw-tool-btn" data-tool="eraser" title="Eraser">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m7 21-4.3-4.3c-1-1-1-2.5 0-3.4l9.6-9.6c1-1 2.5-1 3.4 0l5.6 5.6c1 1 1 2.5 0 3.4L13 21"></path><path d="M22 21H7"></path><path d="m5 11 9 9"></path></svg>
            </button>
            <div style="width: 1px; height: 18px; background: var(--border-subtle); margin: 0 4px;"></div>
            <!-- Color Palette -->
            <div class="color-dot active" data-color="#0f172a" style="background-color: #0f172a;" title="Black"></div>
            <div class="color-dot" data-color="#2563eb" style="background-color: #2563eb;" title="Blue"></div>
            <div class="color-dot" data-color="#dc2626" style="background-color: #dc2626;" title="Red"></div>
            <div class="color-dot" data-color="#16a34a" style="background-color: #16a34a;" title="Green"></div>
            <div class="color-dot" data-color="#ea580c" style="background-color: #ea580c;" title="Orange"></div>
            <div class="color-dot" data-color="#9333ea" style="background-color: #9333ea;" title="Purple"></div>
          </div>
          <div class="drawing-tools-right">
            <span style="font-size: 11px; color: var(--text-muted);">Size:</span>
            <input type="range" class="pen-size-slider" min="1" max="14" step="0.5" value="2.5" style="width: 70px; accent-color: var(--accent-primary);" title="Pen Thickness">
            <button type="button" class="draw-tool-btn btn-undo-draw" title="Undo Stroke">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7v6h6"></path><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path></svg>
            </button>
            <button type="button" class="draw-tool-btn btn-redo-draw" title="Redo Stroke">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 7v6h-6"></path><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3l3 2.7"></path></svg>
            </button>
            <button type="button" class="draw-tool-btn btn-clear-draw" title="Clear Canvas" style="color: var(--error-text);">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
            </button>
          </div>
        </div>
        <div class="drawing-canvas-wrapper">
          <canvas class="handwriting-canvas"></canvas>
        </div>
      </div>
    `;

    this.canvasWrapper = this.container.querySelector(".drawing-canvas-wrapper");
    this.canvas = this.container.querySelector(".handwriting-canvas");
    this.ctx = this.canvas.getContext("2d", { willReadFrequently: true });
  }

  initCanvas() {
    // Handle High-DPI (Retina MacBook and iPad Retina displays)
    const rect = this.canvasWrapper.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const width = rect.width || 750;
    const height = 280;

    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    this.canvas.style.width = `${width}px`;
    this.canvas.style.height = `${height}px`;

    this.ctx.scale(dpr, dpr);
    this.ctx.lineCap = "round";
    this.ctx.lineJoin = "round";
    this.dpr = dpr;
    this.width = width;
    this.height = height;
  }

  attachEvents() {
    // Toolbar Tools Toggle
    const toolBtns = this.container.querySelectorAll(".draw-tool-btn[data-tool]");
    toolBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        toolBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.tool = btn.dataset.tool;
      });
    });

    // Color Dots
    const colorDots = this.container.querySelectorAll(".color-dot");
    colorDots.forEach(dot => {
      dot.addEventListener("click", () => {
        colorDots.forEach(d => d.classList.remove("active"));
        dot.classList.add("active");
        this.color = dot.dataset.color;
        if (this.tool === "eraser") {
          // Switch back to pen on color click
          this.tool = "pen";
          toolBtns.forEach(b => b.classList.toggle("active", b.dataset.tool === "pen"));
        }
      });
    });

    // Line Width Slider
    const sizeSlider = this.container.querySelector(".pen-size-slider");
    sizeSlider.addEventListener("input", (e) => {
      this.lineWidth = parseFloat(e.target.value);
    });

    // Undo / Redo / Clear
    this.container.querySelector(".btn-undo-draw").addEventListener("click", () => this.undo());
    this.container.querySelector(".btn-redo-draw").addEventListener("click", () => this.redo());
    this.container.querySelector(".btn-clear-draw").addEventListener("click", () => this.clear());

    // Pointer Events API (Handles Apple Pencil, Stylus, Finger, Mouse)
    this.canvas.addEventListener("pointerdown", (e) => this.onPointerDown(e));
    this.canvas.addEventListener("pointermove", (e) => this.onPointerMove(e));
    this.canvas.addEventListener("pointerup", (e) => this.onPointerUp(e));
    this.canvas.addEventListener("pointercancel", (e) => this.onPointerUp(e));
    this.canvas.addEventListener("pointerleave", (e) => {
      if (this.currentStroke) this.onPointerUp(e);
    });

    // Resize handling with debounce
    window.addEventListener("resize", () => {
      if (!this.canvasWrapper) return;
      const rect = this.canvasWrapper.getBoundingClientRect();
      if (Math.abs(rect.width - this.width) > 20) {
        const savedImg = this.canvas.toDataURL("image/png");
        this.initCanvas();
        this.loadImage(savedImg);
      }
    });
  }

  getPointerPos(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    // Pressure sensitivity: Apple Pencil provides 0.0 - 1.0; fallback to 0.5 for standard mouse/touch
    const pressure = (e.pressure !== undefined && e.pressure > 0) ? e.pressure : 0.5;
    return { x, y, pressure };
  }

  onPointerDown(e) {
    e.preventDefault();
    this.canvas.setPointerCapture(e.pointerId);

    const pos = this.getPointerPos(e);
    this.currentStroke = {
      tool: this.tool,
      color: this.color,
      width: this.lineWidth,
      points: [pos],
    };

    this.ctx.beginPath();
    this.ctx.moveTo(pos.x, pos.y);
  }

  onPointerMove(e) {
    if (!this.currentStroke) return;
    e.preventDefault();

    const pos = this.getPointerPos(e);
    this.currentStroke.points.push(pos);

    const pts = this.currentStroke.points;
    const prev = pts[pts.length - 2];

    this.ctx.save();

    if (this.currentStroke.tool === "eraser") {
      this.ctx.globalCompositeOperation = "destination-out";
      this.ctx.lineWidth = this.lineWidth * 4;
      this.ctx.beginPath();
      this.ctx.moveTo(prev.x, prev.y);
      this.ctx.lineTo(pos.x, pos.y);
      this.ctx.stroke();
    } else if (this.currentStroke.tool === "highlighter") {
      this.ctx.globalCompositeOperation = "source-over";
      this.ctx.globalAlpha = 0.35;
      this.ctx.strokeStyle = this.currentStroke.color;
      this.ctx.lineWidth = this.lineWidth * 3.5;
      this.ctx.beginPath();
      this.ctx.moveTo(prev.x, prev.y);
      this.ctx.lineTo(pos.x, pos.y);
      this.ctx.stroke();
    } else {
      // Natural Apple Pencil variable thickness according to pressure
      this.ctx.globalCompositeOperation = "source-over";
      this.ctx.globalAlpha = 1.0;
      this.ctx.strokeStyle = this.currentStroke.color;
      const dynamicWidth = this.lineWidth * (0.4 + pos.pressure * 1.2);
      this.ctx.lineWidth = dynamicWidth;

      this.ctx.beginPath();
      this.ctx.moveTo(prev.x, prev.y);
      this.ctx.lineTo(pos.x, pos.y);
      this.ctx.stroke();
    }

    this.ctx.restore();
  }

  onPointerUp(e) {
    if (!this.currentStroke) return;
    try {
      this.canvas.releasePointerCapture(e.pointerId);
    } catch (_) {}

    this.strokes.push(this.currentStroke);
    this.currentStroke = null;
    this.redoStack = []; // clear redo on new action
    this.notifyUpdate();
  }

  undo() {
    if (this.strokes.length === 0) return;
    const popped = this.strokes.pop();
    this.redoStack.push(popped);
    this.redrawAll();
    this.notifyUpdate();
  }

  redo() {
    if (this.redoStack.length === 0) return;
    const restored = this.redoStack.pop();
    this.strokes.push(restored);
    this.redrawAll();
    this.notifyUpdate();
  }

  clear() {
    if (this.strokes.length === 0) return;
    this.redoStack = [...this.strokes];
    this.strokes = [];
    this.ctx.clearRect(0, 0, this.width, this.height);
    this.notifyUpdate();
  }

  redrawAll() {
    this.ctx.clearRect(0, 0, this.width, this.height);

    for (const stroke of this.strokes) {
      if (!stroke.points || stroke.points.length < 2) continue;

      this.ctx.save();
      if (stroke.tool === "eraser") {
        this.ctx.globalCompositeOperation = "destination-out";
        this.ctx.lineWidth = stroke.width * 4;
      } else if (stroke.tool === "highlighter") {
        this.ctx.globalCompositeOperation = "source-over";
        this.ctx.globalAlpha = 0.35;
        this.ctx.strokeStyle = stroke.color;
        this.ctx.lineWidth = stroke.width * 3.5;
      } else {
        this.ctx.globalCompositeOperation = "source-over";
        this.ctx.globalAlpha = 1.0;
        this.ctx.strokeStyle = stroke.color;
        this.ctx.lineWidth = stroke.width;
      }

      this.ctx.beginPath();
      this.ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
      for (let i = 1; i < stroke.points.length; i++) {
        const pt = stroke.points[i];
        if (stroke.tool === "pen") {
          this.ctx.lineWidth = stroke.width * (0.4 + (pt.pressure || 0.5) * 1.2);
        }
        this.ctx.lineTo(pt.x, pt.y);
      }
      this.ctx.stroke();
      this.ctx.restore();
    }
  }

  loadImage(dataUrl) {
    if (!dataUrl) return;
    const img = new Image();
    img.onload = () => {
      this.ctx.clearRect(0, 0, this.width, this.height);
      this.ctx.drawImage(img, 0, 0, this.width, this.height);
    };
    img.src = dataUrl;
  }

  notifyUpdate() {
    if (typeof this.onUpdate === "function") {
      const imgData = this.canvas.toDataURL("image/png");
      this.onUpdate({
        strokes: this.strokes,
        image_data: imgData,
      });
    }
  }

  getData() {
    return {
      strokes: this.strokes,
      image_data: this.canvas.toDataURL("image/png"),
    };
  }
}

window.HandwritingCanvas = HandwritingCanvas;
