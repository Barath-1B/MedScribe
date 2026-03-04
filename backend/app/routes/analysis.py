"""Routes for dataset-1 OCR analysis."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.analysis_service import get_all_documents, compute_overview

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("")
def get_analysis(db: Session = Depends(get_db)):
    """Return OCR evaluation results for all dataset-1 documents."""
    docs = get_all_documents(db)
    # Strip large text fields for listing
    summary = []
    for d in docs:
        row = {k: v for k, v in d.items() if k not in ("ground_truth", "ocr_text")}
        summary.append(row)
    return {"documents": summary, "count": len(summary)}


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    """Return computed KPIs: avg CER/WER/accuracy, snowball, propagation."""
    docs = get_all_documents(db)
    return compute_overview(docs)


@router.get("/full")
def get_full_analysis(db: Session = Depends(get_db)):
    """Return full analysis including OCR text and ground truth."""
    docs = get_all_documents(db)
    return {"documents": docs, "count": len(docs)}
