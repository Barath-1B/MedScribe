"""
Analysis service — runs TrOCR evaluation on handwritten prescription datasets
(HF-MedicalRecords + DoctorHandwritingBD) and caches results in DB.
"""

import logging

import numpy as np
from sqlalchemy.orm import Session

from app.pipeline.ocr import (
    DS_HF_IMAGES, DS_DOC_IMAGES,
    load_hf_ground_truth, load_doctor_handwriting_gt, run_ocr,
)
from app.pipeline.metrics import cer, wer
from app.models import Document

log = logging.getLogger(__name__)


def _build_record(img_path, gt_text: str) -> dict | None:
    """Run OCR on one handwritten prescription and compute metrics against ground truth."""
    ocr_txt = run_ocr(str(img_path), psm=6)

    if not gt_text.strip():
        return None

    c_val, c_info = cer(gt_text, ocr_txt)
    w_val, w_info = wer(gt_text, ocr_txt)

    ref_words = max(w_info.get("ref_words", 1), 1)
    avg_wl = max(c_info.get("ref_len", 1), 1) / ref_words

    return {
        "filename":      img_path.name,
        "image_path":    str(img_path),
        "ground_truth":  gt_text,
        "ocr_text":      ocr_txt,
        "cer":           round(c_val, 2),
        "wer":           round(w_val, 2),
        "accuracy":      round(max(0, 100 - c_val), 2),
        "cer_sub":       c_info.get("sub", 0),
        "cer_del":       c_info.get("del", 0),
        "cer_ins":       c_info.get("ins", 0),
        "cer_ref_len":   c_info.get("ref_len", 0),
        "cer_edit_dist": c_info.get("edit_dist", 0),
        "wer_sub":       w_info.get("sub", 0),
        "wer_del":       w_info.get("del", 0),
        "wer_ins":       w_info.get("ins", 0),
        "wer_ref_words": ref_words,
        "wer_edit_dist": w_info.get("edit_dist", 0),
        "avg_word_len":  round(avg_wl, 1),
    }


def _is_stale_cache(db: Session) -> bool:
    """Check if cached documents have garbage OCR (Tesseract on handwriting → CER > 150%)."""
    sample = db.query(Document).limit(10).all()
    if not sample:
        return False
    bad_count = sum(1 for d in sample if d.cer > 150 or len((d.ocr_text or "").strip()) < 5)
    return bad_count > len(sample) // 2


def _collect_images() -> list[tuple]:
    """Collect all (image_path, ground_truth_text) pairs from both datasets."""
    items = []

    # Dataset 1: HF-MedicalRecords (100 images)
    for entry in load_hf_ground_truth():
        img_path = DS_HF_IMAGES / entry["filename"]
        if img_path.exists():
            items.append((img_path, entry.get("medicines", "")))

    # Dataset 2: DoctorHandwritingBD (89 images)
    for entry in load_doctor_handwriting_gt():
        img_path = DS_DOC_IMAGES / entry["filename"]
        if img_path.exists():
            items.append((img_path, entry.get("medicines", "")))

    return items


def get_all_documents(db: Session) -> list[dict]:
    """
    Return cached analysis from DB. If empty or stale (bad Tesseract output),
    re-run OCR with TrOCR on both handwritten datasets (~189 images).
    """
    existing = db.query(Document).all()
    if existing and not _is_stale_cache(db):
        return [_doc_to_dict(d) for d in existing]

    # Clear stale cache if present
    if existing:
        log.info("Clearing %d stale cached documents (re-running with TrOCR)", len(existing))
        db.query(Document).delete()
        db.commit()

    # Populate from both datasets
    items = _collect_images()
    if not items:
        return []

    total = len(items)
    log.info("Processing %d handwritten prescription images with TrOCR (this may take a while)...", total)

    records = []
    for i, (img_path, gt_text) in enumerate(items):
        log.info("OCR %d/%d: %s", i + 1, total, img_path.name)
        rec = _build_record(img_path, gt_text)
        if rec is None:
            continue
        doc = Document(**rec)
        db.add(doc)
        records.append(rec)

    db.commit()
    log.info("Done! %d documents processed and cached.", len(records))
    return records


def compute_overview(docs: list[dict]) -> dict:
    """Compute KPIs and snowball propagation estimates from analysis results."""
    if not docs:
        return {}

    cers = [d["cer"] for d in docs]
    wers = [d["wer"] for d in docs]
    accs = [d["accuracy"] for d in docs]

    avg_cer = float(np.mean(cers))
    avg_wer = float(np.mean(wers))
    avg_acc = float(np.mean(accs))
    snowball = avg_wer / avg_cer if avg_cer else 0

    p_word_correct = max(0, 1 - avg_wer / 100)
    line_err  = round((1 - p_word_correct ** 8)   * 100, 1)
    sent_err  = round((1 - p_word_correct ** 20)  * 100, 1)
    doc_err   = round((1 - p_word_correct ** 200)  * 100, 1)

    if len(cers) > 1:
        m, _ = np.polyfit(cers, wers, 1)
        trend_slope = round(float(m), 2)
    else:
        trend_slope = snowball

    return {
        "avg_cer":       round(avg_cer, 2),
        "avg_wer":       round(avg_wer, 2),
        "avg_accuracy":  round(avg_acc, 2),
        "snowball_factor": round(snowball, 2),
        "propagation": {
            "char_error":     round(avg_cer, 1),
            "word_error":     round(avg_wer, 1),
            "line_error":     line_err,
            "sentence_error": sent_err,
            "document_error": doc_err,
        },
        "trend_slope":     trend_slope,
        "total_documents": len(docs),
        "dataset":         "Handwritten Prescriptions (HF-MedicalRecords + DoctorHandwritingBD)",
    }


def _doc_to_dict(doc: Document) -> dict:
    return {
        "filename":      doc.filename,
        "image_path":    doc.image_path,
        "ground_truth":  doc.ground_truth,
        "ocr_text":      doc.ocr_text,
        "cer":           doc.cer,
        "wer":           doc.wer,
        "accuracy":      doc.accuracy,
        "cer_sub":       doc.cer_sub,
        "cer_del":       doc.cer_del,
        "cer_ins":       doc.cer_ins,
        "cer_ref_len":   doc.cer_ref_len,
        "cer_edit_dist": doc.cer_edit_dist,
        "wer_sub":       doc.wer_sub,
        "wer_del":       doc.wer_del,
        "wer_ins":       doc.wer_ins,
        "wer_ref_words": doc.wer_ref_words,
        "wer_edit_dist": doc.wer_edit_dist,
        "avg_word_len":  doc.avg_word_len,
    }
