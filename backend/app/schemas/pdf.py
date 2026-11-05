from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class PDFExportResponse(BaseModel):
    notebook_id: str
    filename: str
    download_url: str
    file_size_bytes: int
    page_count: int
    exported_at: str

class PDFImportResponse(BaseModel):
    notebook_id: str
    title: str
    block_count: int
    reconstructed_from: str  # 'embedded_metadata' or 'extracted_content'
    message: str
