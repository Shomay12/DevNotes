import os
import io
import re
import json
import base64
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
import pymupdf
from sqlalchemy.orm import Session
from devnote.app.config import EXPORTS_DIR
from devnote.app.models.notebook import Notebook

PAGE_WIDTH = 595.3   # A4 width in points
PAGE_HEIGHT = 841.9  # A4 height in points
MARGIN_LEFT = 45.0
MARGIN_RIGHT = 45.0
MARGIN_TOP = 50.0
MARGIN_BOTTOM = 55.0
USABLE_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
USABLE_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

class PDFService:
    @staticmethod
    def export_notebook_to_pdf(db: Session, notebook_id: str) -> Dict[str, Any]:
        """
        Exports a canonical notebook to a professional, high-fidelity PDF,
        embedding the full canonical JSON state for lossless round-trip reconstruction.
        """
        notebook = db.query(Notebook).filter(Notebook.id == notebook_id).first()
        if not notebook:
            raise ValueError(f"Notebook with ID {notebook_id} not found.")

        doc = pymupdf.open()
        
        # Helper to create a new page with header and track cursor
        current_page = [doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)]
        cursor_y = [MARGIN_TOP]

        def get_page():
            return current_page[0]

        def check_page_break(needed_height: float):
            if cursor_y[0] + needed_height > PAGE_HEIGHT - MARGIN_BOTTOM:
                current_page[0] = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
                cursor_y[0] = MARGIN_TOP
                # Add a subtle top running header on subsequent pages
                p = get_page()
                p.insert_text(
                    pymupdf.Point(MARGIN_LEFT, 32),
                    f"DevNote — {notebook.title[:50]}",
                    fontsize=8,
                    fontname="helv",
                    color=(0.5, 0.5, 0.5)
                )
                p.draw_line(
                    pymupdf.Point(MARGIN_LEFT, 38),
                    pymupdf.Point(PAGE_WIDTH - MARGIN_RIGHT, 38),
                    color=(0.85, 0.85, 0.85),
                    width=0.5
                )

        # 1. Title Banner
        page = get_page()
        title_text = notebook.title or "Untitled Notebook"
        
        # Banner background
        page.draw_rect(
            pymupdf.Rect(MARGIN_LEFT, cursor_y[0], PAGE_WIDTH - MARGIN_RIGHT, cursor_y[0] + 55),
            color=(0.8, 0.85, 0.95),
            fill=(0.95, 0.97, 1.0)
        )
        page.draw_line(
            pymupdf.Point(MARGIN_LEFT, cursor_y[0]),
            pymupdf.Point(MARGIN_LEFT, cursor_y[0] + 55),
            color=(0.2, 0.4, 0.85),
            width=3.5
        )
        page.insert_text(
            pymupdf.Point(MARGIN_LEFT + 15, cursor_y[0] + 28),
            title_text[:60],
            fontsize=18,
            fontname="hebo",
            color=(0.1, 0.15, 0.3)
        )
        
        # Metadata line
        tags_str = ", ".join(notebook.tags) if notebook.tags else "General"
        date_str = notebook.updated_at.strftime("%b %d, %Y %H:%M UTC") if notebook.updated_at else datetime.now(timezone.utc).strftime("%b %d, %Y")
        meta_line = f"Tags: {tags_str}   |   Last Updated: {date_str}   |   DevNote Interactive"
        page.insert_text(
            pymupdf.Point(MARGIN_LEFT + 15, cursor_y[0] + 44),
            meta_line[:90],
            fontsize=8.5,
            fontname="helv",
            color=(0.4, 0.45, 0.55)
        )
        cursor_y[0] += 70

        # 2. Render Blocks
        blocks = notebook.blocks if isinstance(notebook.blocks, list) else []
        for block in blocks:
            b_type = block.get("type", "paragraph")

            if b_type == "heading":
                level = block.get("level", 2)
                text = block.get("content", "")
                fontsize = 16 if level == 1 else (13 if level == 2 else 11)
                needed = 32
                check_page_break(needed)
                p = get_page()
                cursor_y[0] += 6
                p.insert_text(
                    pymupdf.Point(MARGIN_LEFT, cursor_y[0] + fontsize),
                    text,
                    fontsize=fontsize,
                    fontname="hebo",
                    color=(0.12, 0.14, 0.2)
                )
                cursor_y[0] += fontsize + 10

            elif b_type == "paragraph":
                content = block.get("content", "")
                if not content.strip():
                    cursor_y[0] += 8
                    continue

                lines = content.split("\n")
                for line in lines:
                    wrapped_lines = [line[i:i+85] for i in range(0, max(len(line), 1), 85)]
                    for w in wrapped_lines:
                        check_page_break(16)
                        p = get_page()
                        p.insert_text(
                            pymupdf.Point(MARGIN_LEFT, cursor_y[0] + 11),
                            w,
                            fontsize=9.5,
                            fontname="helv",
                            color=(0.2, 0.22, 0.25)
                        )
                        cursor_y[0] += 15
                cursor_y[0] += 6

            elif b_type == "checklist":
                checked = block.get("checked", False)
                content = block.get("content", "")
                check_page_break(18)
                p = get_page()
                box_char = "[X]" if checked else "[ ]"
                p.insert_text(
                    pymupdf.Point(MARGIN_LEFT, cursor_y[0] + 11),
                    f"{box_char} {content}",
                    fontsize=9.5,
                    fontname="cour" if checked else "helv",
                    color=(0.3, 0.6, 0.3) if checked else (0.2, 0.2, 0.2)
                )
                cursor_y[0] += 18

            elif b_type == "code":
                lang = block.get("language", "python").upper()
                code_text = block.get("code", "")
                output_text = block.get("output", "")
                error_text = block.get("error", "")
                exec_time = block.get("execution_time_ms", 0.0)

                code_lines = code_text.split("\n")
                line_count = len(code_lines)
                code_box_height = max(35, line_count * 13 + 24)

                check_page_break(code_box_height + 25)
                p = get_page()

                # Header bar for code block
                p.draw_rect(
                    pymupdf.Rect(MARGIN_LEFT, cursor_y[0], PAGE_WIDTH - MARGIN_RIGHT, cursor_y[0] + 18),
                    color=(0.85, 0.88, 0.92),
                    fill=(0.92, 0.94, 0.97)
                )
                p.insert_text(
                    pymupdf.Point(MARGIN_LEFT + 8, cursor_y[0] + 13),
                    f"CODE ({lang})",
                    fontsize=7.5,
                    fontname="hebo",
                    color=(0.25, 0.35, 0.5)
                )

                # Code content box
                code_body_rect = pymupdf.Rect(
                    MARGIN_LEFT,
                    cursor_y[0] + 18,
                    PAGE_WIDTH - MARGIN_RIGHT,
                    cursor_y[0] + code_box_height
                )
                p.draw_rect(
                    code_body_rect,
                    color=(0.88, 0.9, 0.93),
                    fill=(0.98, 0.98, 0.99)
                )
                # Left accent border
                p.draw_line(
                    pymupdf.Point(MARGIN_LEFT, cursor_y[0] + 18),
                    pymupdf.Point(MARGIN_LEFT, cursor_y[0] + code_box_height),
                    color=(0.25, 0.45, 0.85),
                    width=2.5
                )

                code_y = cursor_y[0] + 28
                for idx, cl in enumerate(code_lines):
                    # Line number
                    p.insert_text(
                        pymupdf.Point(MARGIN_LEFT + 6, code_y),
                        f"{idx+1:>2}",
                        fontsize=7.5,
                        fontname="cour",
                        color=(0.6, 0.65, 0.7)
                    )
                    # Code string
                    p.insert_text(
                        pymupdf.Point(MARGIN_LEFT + 25, code_y),
                        cl[:80],
                        fontsize=8.5,
                        fontname="cour",
                        color=(0.15, 0.15, 0.2)
                    )
                    code_y += 13

                cursor_y[0] += code_box_height + 4

                # Output panel if output or error exists
                if output_text or error_text:
                    out_lines = (output_text or error_text).split("\n")[:15]
                    out_box_height = max(30, len(out_lines) * 12 + 20)
                    check_page_break(out_box_height + 15)
                    p = get_page()

                    is_error = bool(error_text)
                    fill_col = (1.0, 0.96, 0.96) if is_error else (0.94, 0.98, 0.95)
                    border_col = (0.9, 0.6, 0.6) if is_error else (0.6, 0.85, 0.65)
                    title_col = (0.7, 0.15, 0.15) if is_error else (0.15, 0.5, 0.2)

                    p.draw_rect(
                        pymupdf.Rect(MARGIN_LEFT + 10, cursor_y[0], PAGE_WIDTH - MARGIN_RIGHT, cursor_y[0] + out_box_height),
                        color=border_col,
                        fill=fill_col
                    )
                    p.insert_text(
                        pymupdf.Point(MARGIN_LEFT + 16, cursor_y[0] + 12),
                        f"OUTPUT ({exec_time}ms)" if not is_error else "EXECUTION ERROR",
                        fontsize=7,
                        fontname="hebo",
                        color=title_col
                    )

                    out_y = cursor_y[0] + 23
                    for ol in out_lines:
                        p.insert_text(
                            pymupdf.Point(MARGIN_LEFT + 16, out_y),
                            ol[:85],
                            fontsize=8,
                            fontname="cour",
                            color=(0.2, 0.2, 0.2)
                        )
                        out_y += 12

                    cursor_y[0] += out_box_height + 8
                else:
                    cursor_y[0] += 6

            elif b_type == "drawing":
                # Handwritten Canvas Drawing
                img_data = block.get("image_data")
                caption = block.get("caption", "Handwritten Notes & Sketch")
                drawing_height = 140.0

                check_page_break(drawing_height + 30)
                p = get_page()

                # Drawing frame
                draw_rect = pymupdf.Rect(
                    MARGIN_LEFT,
                    cursor_y[0],
                    PAGE_WIDTH - MARGIN_RIGHT,
                    cursor_y[0] + drawing_height
                )
                p.draw_rect(draw_rect, color=(0.85, 0.87, 0.9), fill=(0.99, 0.99, 1.0))

                # Header tag
                p.insert_text(
                    pymupdf.Point(MARGIN_LEFT + 8, cursor_y[0] + 12),
                    f"HANDWRITTEN NOTE: {caption}",
                    fontsize=7.5,
                    fontname="hebo",
                    color=(0.4, 0.45, 0.6)
                )

                if img_data and "base64," in img_data:
                    try:
                        raw_base64 = img_data.split("base64,")[1]
                        img_bytes = base64.b64decode(raw_base64)
                        img_rect = pymupdf.Rect(
                            MARGIN_LEFT + 6,
                            cursor_y[0] + 16,
                            PAGE_WIDTH - MARGIN_RIGHT - 6,
                            cursor_y[0] + drawing_height - 6
                        )
                        p.insert_image(img_rect, stream=img_bytes)
                    except Exception:
                        p.insert_text(
                            pymupdf.Point(MARGIN_LEFT + 20, cursor_y[0] + 60),
                            "[Handwritten Canvas Drawing]",
                            fontsize=10,
                            fontname="helv",
                            color=(0.5, 0.5, 0.5)
                        )
                else:
                    p.insert_text(
                        pymupdf.Point(MARGIN_LEFT + 20, cursor_y[0] + 60),
                        "[Handwritten Canvas Drawing]",
                        fontsize=10,
                        fontname="helv",
                        color=(0.5, 0.5, 0.5)
                    )

                cursor_y[0] += drawing_height + 10

            elif b_type == "math":
                expr = block.get("expression") or block.get("content", "")
                check_page_break(32)
                p = get_page()
                p.draw_rect(
                    pymupdf.Rect(MARGIN_LEFT, cursor_y[0], PAGE_WIDTH - MARGIN_RIGHT, cursor_y[0] + 26),
                    color=(0.85, 0.85, 0.9),
                    fill=(0.97, 0.97, 0.99)
                )
                p.insert_text(
                    pymupdf.Point(MARGIN_LEFT + 12, cursor_y[0] + 17),
                    f"Formula:  {expr}",
                    fontsize=9.5,
                    fontname="cour",
                    color=(0.1, 0.2, 0.4)
                )
                cursor_y[0] += 34

            elif b_type == "table":
                rows = block.get("rows", [])
                if rows:
                    row_height = 18.0
                    table_height = len(rows) * row_height + 10
                    check_page_break(table_height)
                    p = get_page()

                    table_top = cursor_y[0]
                    col_width = (PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT) / max(len(rows[0]), 1)

                    for r_idx, row in enumerate(rows):
                        y_pos = table_top + r_idx * row_height
                        # Header row background
                        if r_idx == 0:
                            p.draw_rect(
                                pymupdf.Rect(MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_RIGHT, y_pos + row_height),
                                color=(0.8, 0.85, 0.9),
                                fill=(0.92, 0.94, 0.98)
                            )
                        for c_idx, cell in enumerate(row):
                            x_pos = MARGIN_LEFT + c_idx * col_width
                            # Draw cell outline
                            p.draw_rect(
                                pymupdf.Rect(x_pos, y_pos, x_pos + col_width, y_pos + row_height),
                                color=(0.85, 0.85, 0.88)
                            )
                            p.insert_text(
                                pymupdf.Point(x_pos + 6, y_pos + 13),
                                str(cell)[:20],
                                fontsize=8.5,
                                fontname="hebo" if r_idx == 0 else "helv",
                                color=(0.15, 0.2, 0.3) if r_idx == 0 else (0.2, 0.2, 0.2)
                            )
                    cursor_y[0] += table_height + 6

        # 3. Add Page Footers with running page numbers
        total_pages = len(doc)
        for idx, pg in enumerate(doc):
            pg.draw_line(
                pymupdf.Point(MARGIN_LEFT, PAGE_HEIGHT - 35),
                pymupdf.Point(PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - 35),
                color=(0.88, 0.88, 0.88),
                width=0.5
            )
            pg.insert_text(
                pymupdf.Point(MARGIN_LEFT, PAGE_HEIGHT - 22),
                "DevNote Workspace • Interactive Technical Notebook",
                fontsize=7.5,
                fontname="helv",
                color=(0.55, 0.55, 0.55)
            )
            pg.insert_text(
                pymupdf.Point(PAGE_WIDTH - MARGIN_RIGHT - 60, PAGE_HEIGHT - 22),
                f"Page {idx+1} of {total_pages}",
                fontsize=7.5,
                fontname="helv",
                color=(0.55, 0.55, 0.55)
            )

        # 4. CRITICAL: Embed Canonical Notebook State for Lossless Round-Trip Import
        canonical_state = {
            "devnote_version": "1.0",
            "notebook_id": notebook.id,
            "title": notebook.title,
            "description": notebook.description,
            "tags": notebook.tags,
            "blocks": notebook.blocks,
            "version": notebook.version,
            "created_at": notebook.created_at.isoformat() if notebook.created_at else None,
            "updated_at": notebook.updated_at.isoformat() if notebook.updated_at else None,
        }
        json_bytes = json.dumps(canonical_state, ensure_ascii=False).encode("utf-8")
        doc.embfile_add("devnote_state.json", json_bytes, filename="devnote_state.json", desc="Canonical DevNote Document State")

        # Save PDF to exports directory
        safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', notebook.title.strip()) or "notebook"
        filename = f"{safe_title}_{notebook.id[:8]}.pdf"
        output_path = EXPORTS_DIR / filename
        doc.save(str(output_path))
        doc.close()

        # Update notebook export record
        file_size = os.path.getsize(output_path)
        notebook.pdf_export_path = str(output_path)
        notebook.pdf_exported_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "notebook_id": notebook.id,
            "filename": filename,
            "download_url": f"/api/notebooks/{notebook.id}/pdf",
            "file_size_bytes": file_size,
            "page_count": total_pages,
            "exported_at": notebook.pdf_exported_at.isoformat()
        }

    @staticmethod
    def import_notebook_from_pdf(
        db: Session,
        pdf_bytes: bytes,
        target_notebook_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Imports a notebook from PDF.
        - If embedded DevNote state exists: reconstructs the exact document state.
        - If target_notebook_id is provided, updates that existing notebook (NO DUPLICATES).
        - If standard PDF: extracts text, detects headings, code blocks, and reconstructs editable blocks.
        """
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        
        # Check for embedded DevNote state
        emb_names = doc.embfile_names() if hasattr(doc, "embfile_names") else []
        if "devnote_state.json" in emb_names:
            state_data = doc.embfile_get("devnote_state.json")
            state = json.loads(state_data.decode("utf-8"))
            doc.close()

            incoming_id = state.get("notebook_id")
            title = state.get("title", "Imported Notebook")
            description = state.get("description", "")
            tags = state.get("tags", [])
            blocks = state.get("blocks", [])

            # Check if target notebook was specified or if the notebook already exists in DB
            target_id = target_notebook_id or incoming_id
            existing = None
            if target_id:
                existing = db.query(Notebook).filter(Notebook.id == target_id).first()

            if existing:
                # Update existing notebook - NEVER create duplicate!
                existing.title = title
                existing.description = description
                existing.tags = tags
                existing.blocks = blocks
                existing.version = (existing.version or 1) + 1
                existing.updated_at = datetime.now(timezone.utc)
                existing.last_edited_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(existing)
                return {
                    "notebook_id": existing.id,
                    "title": existing.title,
                    "block_count": len(blocks),
                    "reconstructed_from": "embedded_metadata",
                    "message": f"Successfully updated canonical notebook '{existing.title}' without duplicates."
                }
            else:
                # Create as new persistent notebook
                new_nb = Notebook(
                    id=incoming_id or str(uuid.uuid4()),
                    title=title,
                    description=description,
                    tags=tags,
                    blocks=blocks,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    last_edited_at=datetime.now(timezone.utc),
                    version=1
                )
                db.add(new_nb)
                db.commit()
                db.refresh(new_nb)
                return {
                    "notebook_id": new_nb.id,
                    "title": new_nb.title,
                    "block_count": len(blocks),
                    "reconstructed_from": "embedded_metadata",
                    "message": f"Successfully reconstructed notebook '{new_nb.title}' from DevNote PDF."
                }

        # Otherwise: Standard PDF extraction & heuristic reconstruction
        extracted_blocks = []
        pdf_title = "Imported Document"

        # Code detection pattern
        code_pattern = re.compile(r'^\s*(def |class |import |from |for |while |if |return |console\.log|const |let |var |function )')

        for page_num in range(len(doc)):
            page = doc[page_num]
            text_blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)
            
            for tb in text_blocks:
                text = tb[4].strip()
                if not text:
                    continue

                # Header detection on page 1
                if page_num == 0 and not extracted_blocks and len(text) < 60 and ("\n" not in text or len(text.split("\n")) <= 2):
                    pdf_title = text.split("\n")[0]
                    extracted_blocks.append({
                        "id": f"block-import-h1-{page_num}",
                        "type": "heading",
                        "level": 1,
                        "content": pdf_title
                    })
                    continue

                # Check if text looks like a code block
                lines = text.split("\n")
                code_matching_lines = sum(1 for line in lines if code_pattern.search(line))
                if code_matching_lines >= 2 or (len(lines) >= 3 and any("{" in l or ";" in l for l in lines) and any("def " in l or "function " in l or "import " in l for l in lines)):
                    is_py = any("def " in l or "import " in l or "print(" in l for l in lines)
                    extracted_blocks.append({
                        "id": f"block-import-code-{len(extracted_blocks)}",
                        "type": "code",
                        "language": "python" if is_py else "javascript",
                        "code": text,
                        "output": "",
                        "error": "",
                        "execution_time_ms": 0.0,
                        "status": "idle"
                    })
                elif len(text) < 80 and not text.endswith(".") and len(lines) == 1:
                    # Heading block
                    extracted_blocks.append({
                        "id": f"block-import-h2-{len(extracted_blocks)}",
                        "type": "heading",
                        "level": 2,
                        "content": text
                    })
                else:
                    # Paragraph block
                    extracted_blocks.append({
                        "id": f"block-import-p-{len(extracted_blocks)}",
                        "type": "paragraph",
                        "content": text
                    })

        doc.close()

        # If empty document
        if not extracted_blocks:
            extracted_blocks = [{
                "id": "block-import-default",
                "type": "paragraph",
                "content": "Imported content was empty or unreadable."
            }]

        if target_notebook_id:
            existing = db.query(Notebook).filter(Notebook.id == target_notebook_id).first()
            if existing:
                existing.blocks = (existing.blocks or []) + extracted_blocks
                existing.updated_at = datetime.now(timezone.utc)
                existing.last_edited_at = datetime.now(timezone.utc)
                db.commit()
                return {
                    "notebook_id": existing.id,
                    "title": existing.title,
                    "block_count": len(extracted_blocks),
                    "reconstructed_from": "extracted_content",
                    "message": f"Appended {len(extracted_blocks)} blocks to '{existing.title}'."
                }

        # Create new notebook from extracted content
        import uuid
        new_nb = Notebook(
            id=str(uuid.uuid4()),
            title=pdf_title,
            description="Reconstructed from PDF upload",
            tags=["imported"],
            blocks=extracted_blocks,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_edited_at=datetime.now(timezone.utc),
            version=1
        )
        db.add(new_nb)
        db.commit()
        db.refresh(new_nb)

        return {
            "notebook_id": new_nb.id,
            "title": new_nb.title,
            "block_count": len(extracted_blocks),
            "reconstructed_from": "extracted_content",
            "message": f"Reconstructed notebook '{new_nb.title}' with {len(extracted_blocks)} blocks."
        }
