"""
Analysis service — runs OCR evaluation on dataset-1 and caches results in DB.
Ported from dashboard.py load_analysis() + KPI computations.
"""

import numpy as np
from sqlalchemy.orm import Session

from app.pipeline.ocr import DS1_IMAGES, DS1_ANNOTATIONS, gt_from_funsd_json, run_ocr
from app.pipeline.metrics import cer, wer
from app.models import Document


def _build_record(img_path, ann_path) -> dict:
    """Run OCR on one document and compute metrics."""
    gt = gt_from_funsd_json(ann_path)
    ocr_txt = run_ocr(img_path)
    c_val, c_info = cer(gt, ocr_txt)
    w_val, w_info = wer(gt, ocr_txt)

    ref_words = max(w_info.get("ref_words", 1), 1)
    avg_wl = max(c_info.get("ref_len", 1), 1) / ref_words

    return {
        "filename":      img_path.name,
        "image_path":    str(img_path),
        "ground_truth":  gt,
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


def get_all_documents(db: Session) -> list[dict]:
    """
    Return cached analysis from DB. If empty, run OCR on all dataset-1 docs,
    store in the documents table, and return them.
    """
    existing = db.query(Document).all()
    if existing:
        return [_doc_to_dict(d) for d in existing]

    # First run — populate DB
    image_files = sorted(DS1_IMAGES.glob("*.png"))
    records = []
    for img_path in image_files:
        ann_path = DS1_ANNOTATIONS / (img_path.stem + ".json")
        if not ann_path.exists():
            continue
        rec = _build_record(img_path, ann_path)
        doc = Document(**rec)
        db.add(doc)
        records.append(rec)

    db.commit()
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

    p_word_correct = 1 - avg_wer / 100
    line_err  = round((1 - p_word_correct ** 8)   * 100, 1)
    sent_err  = round((1 - p_word_correct ** 20)  * 100, 1)
    doc_err   = round((1 - p_word_correct ** 200)  * 100, 1)

    # Trend line slope (CER → WER)
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
