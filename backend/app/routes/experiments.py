"""Routes for running pipeline experiments."""

import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GroundTruthNote, Experiment, StageResult
from app.pipeline.runner import run_pipeline

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


class RunRequest(BaseModel):
    note_ids: list[int]
    error_rates: list[float] = [0.0, 0.02, 0.05, 0.10, 0.15, 0.20]
    error_type: str = "mixed"


@router.post("/run")
def run_experiments(req: RunRequest, db: Session = Depends(get_db)):
    """Run the 4-stage pipeline for each note x error_rate combination."""
    results = []

    for note_id in req.note_ids:
        note = db.query(GroundTruthNote).filter(GroundTruthNote.id == note_id).first()
        if not note:
            raise HTTPException(404, f"Note {note_id} not found")

        for rate in req.error_rates:
            exp = Experiment(
                note_id=note_id,
                error_rate=rate,
                error_type=req.error_type,
                status="running",
            )
            db.add(exp)
            db.flush()

            t0 = time.time()
            # If note has real OCR text and error_rate is 0, use real OCR mode
            use_real_ocr = note.ocr_text and rate == 0.0
            result = run_pipeline(
                ground_truth_text=note.true_text,
                ground_truth_summary=note.true_summary or "",
                ground_truth_topic=note.true_topic or "",
                error_rate=rate,
                error_type=req.error_type,
                ocr_text=note.ocr_text if use_real_ocr else None,
            )
            exp.run_time_seconds = round(time.time() - t0, 3)
            exp.status = "completed"

            # Store stage results
            s = result["stages"]
            stage_map = [
                (1, "ocr", s["ocr"]),
                (2, "spell_correction", s["spell_correction"]),
                (3, "summarization", s["summarization"]),
                (4, "classification", s["classification"]),
            ]
            for order, name, data in stage_map:
                sr = StageResult(
                    experiment_id=exp.id,
                    stage_name=name,
                    stage_order=order,
                    output_text=data.get("text"),
                    cer=data.get("cer"),
                    wer=data.get("wer"),
                    error_recovery_rate=data.get("recovery_pct"),
                    corrections_made=data.get("corrections_made"),
                    rouge_1=data.get("rouge_1"),
                    rouge_2=data.get("rouge_2"),
                    rouge_l=data.get("rouge_l"),
                    topic_correct=data.get("topic_correct"),
                    topic_confidence=data.get("confidence"),
                    predicted_topic=data.get("predicted_topic"),
                    all_scores=data.get("all_scores"),
                    processing_time_ms=data.get("processing_time_ms"),
                )
                db.add(sr)

            results.append({
                "note_id":       note_id,
                "note_title":    note.title,
                "error_rate":    rate,
                "experiment_id": exp.id,
                "status":        exp.status,
                "mode":          "real_ocr" if use_real_ocr else "simulated",
            })

    db.commit()
    return {"status": "done", "total_runs": len(results), "experiments": results}


@router.get("")
def list_experiments(db: Session = Depends(get_db)):
    """List all experiments with their stage results."""
    experiments = (
        db.query(Experiment)
        .order_by(Experiment.created_at.desc())
        .all()
    )
    return [
        {
            "id":              e.id,
            "note_id":         e.note_id,
            "note_title":      e.note.title if e.note else "Unknown",
            "error_rate":      e.error_rate,
            "error_type":      e.error_type,
            "status":          e.status,
            "mode":            "real_ocr" if (e.note and e.note.ocr_text and e.error_rate == 0.0) else "simulated",
            "run_time_seconds": e.run_time_seconds,
            "created_at":      e.created_at.isoformat() if e.created_at else None,
            "stage_results": [
                {
                    "stage_name":     sr.stage_name,
                    "stage_order":    sr.stage_order,
                    "cer":            sr.cer,
                    "wer":            sr.wer,
                    "rouge_1":        sr.rouge_1,
                    "rouge_2":        sr.rouge_2,
                    "rouge_l":        sr.rouge_l,
                    "topic_correct":  sr.topic_correct,
                    "topic_confidence": sr.topic_confidence,
                    "predicted_topic":  sr.predicted_topic,
                    "error_recovery_rate": sr.error_recovery_rate,
                    "corrections_made":    sr.corrections_made,
                }
                for sr in sorted(e.stage_results, key=lambda s: s.stage_order)
            ],
        }
        for e in experiments
    ]
