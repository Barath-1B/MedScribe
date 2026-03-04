"""
Pipeline service — runs the full 4-stage pipeline on dataset-1 documents.
Ported from dashboard.py load_pipeline_results().
"""

from functools import lru_cache

from app.pipeline.ocr import DS1_IMAGES, DS1_ANNOTATIONS, gt_from_funsd_json, run_ocr
from app.pipeline.runner import run_pipeline


@lru_cache(maxsize=1)
def get_pipeline_results() -> list[dict]:
    """Run full 4-stage pipeline on every dataset-1 document (cached in-memory)."""
    image_files = sorted(DS1_IMAGES.glob("*.png"))
    records = []

    for img_path in image_files:
        ann_path = DS1_ANNOTATIONS / (img_path.stem + ".json")
        if not ann_path.exists():
            continue

        gt = gt_from_funsd_json(ann_path)
        ocr_txt = run_ocr(img_path)

        # Use first 30% of GT as surrogate summary reference
        words = gt.split()
        gt_summary = " ".join(words[:max(5, len(words) // 3)])

        result = run_pipeline(
            ground_truth_text=gt,
            ground_truth_summary=gt_summary,
            ground_truth_topic="",
            ocr_text=ocr_txt,
        )

        s = result["stages"]
        records.append({
            "filename":        img_path.name,
            "image_path":      str(img_path),
            "s1_cer":          s["ocr"]["cer"],
            "s1_wer":          s["ocr"]["wer"],
            "s2_cer":          s["spell_correction"]["cer"],
            "s2_wer":          s["spell_correction"]["wer"],
            "s2_recovery":     s["spell_correction"]["recovery_pct"],
            "s2_corrections":  s["spell_correction"]["corrections_made"],
            "s3_rouge1":       s["summarization"]["rouge_1"],
            "s3_rouge2":       s["summarization"]["rouge_2"],
            "s3_rougel":       s["summarization"]["rouge_l"],
            "s4_topic":        s["classification"]["predicted_topic"],
            "s4_confidence":   s["classification"]["confidence"],
            "s4_all_scores":   s["classification"]["all_scores"],
        })

    return records
