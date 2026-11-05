import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from devnote.app.database import get_db
from devnote.app.schemas.pdf import PDFExportResponse, PDFImportResponse
from devnote.app.services.pdf_service import PDFService
from devnote.app.models.notebook import Notebook

router = APIRouter(prefix="/api/notebooks", tags=["pdf"])

@router.post("/{notebook_id}/export", response_model=PDFExportResponse)
def export_notebook(notebook_id: str, db: Session = Depends(get_db)):
    try:
        result = PDFService.export_notebook_to_pdf(db, notebook_id)
        return PDFExportResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")

@router.post("/import", response_model=PDFImportResponse)
async def import_notebook(
    file: UploadFile = File(...),
    target_notebook_id: str = Form(None),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for import.")

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        result = PDFService.import_notebook_from_pdf(
            db=db,
            pdf_bytes=content,
            target_notebook_id=target_notebook_id if target_notebook_id else None
        )
        return PDFImportResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF import failed: {str(e)}")

@router.get("/{notebook_id}/pdf")
def download_notebook_pdf(notebook_id: str, db: Session = Depends(get_db)):
    notebook = db.query(Notebook).filter(Notebook.id == notebook_id).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    pdf_path = notebook.pdf_export_path
    if not pdf_path or not os.path.exists(pdf_path):
        # Generate on the fly if not yet exported
        res = PDFService.export_notebook_to_pdf(db, notebook_id)
        pdf_path = notebook.pdf_export_path

    filename = os.path.basename(pdf_path)
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )
