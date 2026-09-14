"""File download router (PDF outputs)."""

import os
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from models.video import find_output_by_job_id

router = APIRouter(prefix="/files", tags=["Files"])

@router.get("/pdf/{job_id}")
async def get_pdf(job_id: str):
    out = await find_output_by_job_id(job_id)
    if not out or not out.get("pdfPath"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF output not found")
    pdf_path = out["pdfPath"]
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF file missing from storage")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"videonotes_{job_id}.pdf")
