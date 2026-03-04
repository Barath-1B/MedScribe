"""Routes for exporting results."""

import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.analysis_service import get_all_documents

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    """Export OCR analysis results as a downloadable CSV file."""
    docs = get_all_documents(db)
    if not docs:
        return {"error": "No analysis data available"}

    output = io.StringIO()
    fieldnames = [
        "filename", "cer", "wer", "accuracy",
        "cer_sub", "cer_del", "cer_ins",
        "wer_sub", "wer_del", "wer_ins",
        "cer_ref_len", "wer_ref_words",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(docs)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ocr_results.csv"},
    )
