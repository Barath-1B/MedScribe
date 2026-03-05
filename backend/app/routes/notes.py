"""Routes for CRUD operations on ground truth notes."""

from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GroundTruthNote

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.get("")
def list_notes(db: Session = Depends(get_db)):
    """List all ground truth notes."""
    notes = db.query(GroundTruthNote).order_by(GroundTruthNote.created_at.desc()).all()
    return [
        {
            "id":           n.id,
            "title":        n.title,
            "true_text":    n.true_text,
            "true_topic":   n.true_topic,
            "subject_area": n.subject_area,
            "word_count":   n.word_count,
            "created_at":   n.created_at.isoformat() if n.created_at else None,
        }
        for n in notes
    ]


@router.post("")
def create_note(
    title: str = Form(...),
    true_text: str = Form(...),
    true_summary: str = Form(""),
    true_topic: str = Form(""),
    subject_area: str = Form(""),
    db: Session = Depends(get_db),
):
    """Upload a new ground truth clinical note."""
    note = GroundTruthNote(
        title=title,
        true_text=true_text,
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
            "true_topic": note.true_topic,
            "word_count": note.word_count,
        },
    }


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
        "true_summary": note.true_summary,
        "true_topic":   note.true_topic,
        "subject_area": note.subject_area,
        "word_count":   note.word_count,
    }


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note and all its experiments (cascade)."""
    note = db.query(GroundTruthNote).filter(GroundTruthNote.id == note_id).first()
    if not note:
        raise HTTPException(404, "Note not found")
    db.delete(note)
    db.commit()
    return {"status": "deleted", "note_id": note_id}
