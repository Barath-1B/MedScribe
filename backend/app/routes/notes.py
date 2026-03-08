"""Routes for CRUD operations on ground truth notes + OCR preview."""

import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GroundTruthNote
from app.pipeline.ocr import run_ocr

_UPLOADS = Path(__file__).parents[2] / "uploads"
_UPLOADS.mkdir(exist_ok=True)

router = APIRouter(prefix="/api/notes", tags=["notes"])


# ── List notes ────────────────────────────────────────────────────────────────

@router.get("")
def list_notes(db: Session = Depends(get_db)):
    """List all ground truth notes."""
    notes = db.query(GroundTruthNote).order_by(GroundTruthNote.created_at.desc()).all()
    return [
        {
            "id":           n.id,
            "title":        n.title,
            "true_text":    n.true_text,
            "ocr_text":     n.ocr_text,
            "ocr_method":   n.ocr_method,
            "image_path":   n.image_path,
            "has_image":    bool(n.image_path),
            "has_ocr":      bool(n.ocr_text),
            "true_topic":   n.true_topic,
            "subject_area": n.subject_area,
            "word_count":   n.word_count,
            "created_at":   n.created_at.isoformat() if n.created_at else None,
        }
        for n in notes
    ]


# ── OCR preview (upload image, get OCR text back, don't save) ─────────────────

@router.post("/ocr-preview")
async def ocr_preview(image: UploadFile = File(...)):
    """Upload an image, run Tesseract, return OCR text without saving to DB."""
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image (jpg, png, etc.)")

    # Save temp file
    suffix = Path(image.filename).suffix or ".jpg"
    temp_name = f"preview_{uuid.uuid4().hex[:8]}{suffix}"
    temp_path = _UPLOADS / temp_name
    try:
        with open(temp_path, "wb") as f:
            content = await image.read()
            f.write(content)

        ocr_text = run_ocr(str(temp_path))
        return {
            "ocr_text": ocr_text,
            "filename": image.filename,
            "temp_image": temp_name,
        }
    except Exception as e:
        raise HTTPException(500, f"OCR failed: {str(e)}")
    finally:
        if temp_path.exists():
            temp_path.unlink()


# ── Create note (with optional image upload) ──────────────────────────────────

@router.post("")
async def create_note(
    title: str = Form(...),
    true_text: str = Form(...),
    ocr_text: str = Form(""),
    true_summary: str = Form(""),
    true_topic: str = Form(""),
    subject_area: str = Form(""),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    """Create a new note. Optionally upload an image (OCR text should come from preview)."""
    image_path = None
    ocr_method = None

    if image and image.filename:
        suffix = Path(image.filename).suffix or ".jpg"
        saved_name = f"note_{uuid.uuid4().hex[:8]}{suffix}"
        saved_path = _UPLOADS / saved_name
        with open(saved_path, "wb") as f:
            content = await image.read()
            f.write(content)
        image_path = str(saved_path)
        ocr_method = "tesseract"

    note = GroundTruthNote(
        title=title,
        true_text=true_text,
        ocr_text=ocr_text or None,
        ocr_method=ocr_method if ocr_text else None,
        image_path=image_path,
        true_summary=true_summary,
        true_topic=true_topic,
        subject_area=subject_area or None,
        word_count=len(true_text.split()),
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return {
        "status": "created",
        "note": {
            "id":         note.id,
            "title":      note.title,
            "has_image":  bool(note.image_path),
            "has_ocr":    bool(note.ocr_text),
            "word_count": note.word_count,
        },
    }


# ── Serve uploaded note images ────────────────────────────────────────────────

@router.get("/{note_id}/image")
def get_note_image(note_id: int, db: Session = Depends(get_db)):
    """Serve the uploaded image for a note."""
    note = db.query(GroundTruthNote).filter(GroundTruthNote.id == note_id).first()
    if not note or not note.image_path:
        raise HTTPException(404, "Image not found")
    p = Path(note.image_path)
    if not p.is_file():
        raise HTTPException(404, "Image file missing from disk")
    media = "image/png" if p.suffix == ".png" else "image/jpeg"
    return FileResponse(str(p), media_type=media)


# ── Get single note ───────────────────────────────────────────────────────────

@router.get("/{note_id}")
def get_note(note_id: int, db: Session = Depends(get_db)):
    """Get a single note with full text."""
    note = db.query(GroundTruthNote).filter(GroundTruthNote.id == note_id).first()
    if not note:
        raise HTTPException(404, "Note not found")
    return {
        "id":           note.id,
        "title":        note.title,
        "true_text":    note.true_text,
        "ocr_text":     note.ocr_text,
        "ocr_method":   note.ocr_method,
        "has_image":    bool(note.image_path),
        "true_summary": note.true_summary,
        "true_topic":   note.true_topic,
        "subject_area": note.subject_area,
        "word_count":   note.word_count,
    }


# ── Delete note ───────────────────────────────────────────────────────────────

@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note and all its experiments (cascade)."""
    note = db.query(GroundTruthNote).filter(GroundTruthNote.id == note_id).first()
    if not note:
        raise HTTPException(404, "Note not found")
    # Clean up uploaded image
    if note.image_path:
        p = Path(note.image_path)
        if p.is_file():
            p.unlink()
    db.delete(note)
    db.commit()
    return {"status": "deleted", "note_id": note_id}
