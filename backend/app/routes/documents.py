"""Routes for serving individual document images and diffs."""

import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.pipeline.ocr import DS1_IMAGES
from app.services.analysis_service import get_all_documents
from app.services.diff_service import html_diff

router = APIRouter(prefix="/api/documents", tags=["documents"])

_SAFE_FILENAME = re.compile(r'^[\w.-]+\.png$')


@router.get("/{filename}/image")
def get_image(filename: str):
    """Serve a dataset-1 document image."""
    if not _SAFE_FILENAME.match(filename):
        raise HTTPException(400, "Invalid filename")
    path = DS1_IMAGES / filename
    if not path.is_file():
        raise HTTPException(404, "Image not found")
    return FileResponse(str(path), media_type="image/png")


@router.get("/{filename}/diff")
def get_diff(filename: str, db: Session = Depends(get_db)):
    """Return HTML diff between OCR output and ground truth for a document."""
    docs = get_all_documents(db)
    doc = next((d for d in docs if d["filename"] == filename), None)
    if not doc:
        raise HTTPException(404, "Document not found")

    return {
        "filename":     filename,
        "diff_html":    html_diff(doc["ocr_text"], doc["ground_truth"]),
        "ocr_text":     doc["ocr_text"],
        "ground_truth": doc["ground_truth"],
    }
