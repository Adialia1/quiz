"""
Documents API Routes
Serves static documents like terms and conditions
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Path to static documents
DOCUMENTS_DIR = Path(__file__).parent.parent / "static" / "documents"


@router.get("/terms")
async def get_terms_pdf():
    """
    Get terms and conditions PDF
    Returns the PDF file directly with proper headers
    """
    pdf_path = DOCUMENTS_DIR / "terms.pdf"

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Terms PDF not found")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename="terms.pdf",
        headers={
            "Content-Disposition": "inline; filename=terms.pdf",
            "Access-Control-Allow-Origin": "*",
        }
    )
