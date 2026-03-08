"""Routes for serving document images, diffs, and dataset gallery."""

import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.pipeline.ocr import (
    DS_HF_IMAGES, DS_DOC_IMAGES,
    load_hf_ground_truth, load_doctor_handwriting_gt,
)
from app.services.analysis_service import get_all_documents
from app.services.diff_service import html_diff

router = APIRouter(prefix="/api/documents", tags=["documents"])

_SAFE_FILENAME = re.compile(r'^[\w .()-]+\.(png|jpg|jpeg)$', re.IGNORECASE)

# Both image directories to search when serving images
_IMAGE_DIRS = [DS_HF_IMAGES, DS_DOC_IMAGES]


def _find_image(filename: str):
    """Find an image file across all dataset directories."""
    for d in _IMAGE_DIRS:
        path = d / filename
        if path.is_file():
            return path
    return None


@router.get("/{filename}/image")
def get_image(filename: str):
    """Serve a dataset document image (handwritten prescription)."""
    if not _SAFE_FILENAME.match(filename):
        raise HTTPException(400, "Invalid filename")
    path = _find_image(filename)
    if not path:
        raise HTTPException(404, "Image not found")
    media = "image/png" if filename.endswith(".png") else "image/jpeg"
    return FileResponse(str(path), media_type=media)


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


# ── Dataset Gallery ───────────────────────────────────────────────────────────

@router.get("/gallery/list")
def get_gallery():
    """Return list of handwritten prescription images from both datasets."""
    gallery = []

    # HF-MedicalRecords
    for entry in load_hf_ground_truth():
        img_path = DS_HF_IMAGES / entry["filename"]
        if img_path.exists():
            gallery.append({
                "filename":   entry["filename"],
                "medicines":  entry.get("medicines", ""),
                "dataset":    "HF-MedicalRecords",
                "image_url":  f"/api/documents/{entry['filename']}/image",
            })

    # DoctorHandwritingBD
    for entry in load_doctor_handwriting_gt():
        img_path = DS_DOC_IMAGES / entry["filename"]
        if img_path.exists():
            gallery.append({
                "filename":   entry["filename"],
                "medicines":  entry.get("medicines", ""),
                "dataset":    "DoctorHandwritingBD",
                "image_url":  f"/api/documents/{entry['filename']}/image",
            })

    return gallery
