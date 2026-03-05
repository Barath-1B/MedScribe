"""Pipeline runner — orchestrates the 4-stage clinical text processing pipeline.

Tracks snowball effect: CER/WER measured at every stage to show how errors
cascade and amplify through the pipeline.
"""

import time

from app.pipeline.metrics import cer as _cer, wer as _wer, error_recovery_rate, compute_rouge
from app.pipeline.error_injector import inject_errors
from app.pipeline.spell_correction import spell_correct
from app.pipeline.summarizer import extractive_summarize
from app.pipeline.classifier import classify_topic


def run_pipeline(
    ground_truth_text: str,
    ground_truth_summary: str = "",
    ground_truth_topic: str = "",
    error_rate: float = 0.0,
    error_type: str = "mixed",
    ocr_text: str = None,
) -> dict:
    """
    Run the full 4-stage pipeline and return per-stage metrics.

    Snowball tracking: CER and WER are measured at every stage against the
    original ground truth, so you can see exactly how errors grow or shrink.

    Pass ocr_text for real-OCR mode; omit to simulate via error injection.
    """
    t0 = time.time()

    # ── Stage 0: Baseline (ground truth) ──────────────────────────────────
    s0_cer, s0_cer_info = 0.0, {}
    s0_wer, s0_wer_info = 0.0, {}

    # ── Stage 1: OCR / Error Injection ────────────────────────────────────
    if ocr_text is not None:
        stage1_text = ocr_text
        method = "real_tesseract"
    else:
        stage1_text = inject_errors(ground_truth_text, error_rate, error_type)
        method = f"simulated_{error_type}"

    s1_cer, s1_cer_info = _cer(ground_truth_text, stage1_text)
    s1_wer, s1_wer_info = _wer(ground_truth_text, stage1_text)

    # ── Stage 2: Spell Correction ─────────────────────────────────────────
    sc = spell_correct(stage1_text)
    s2_text = sc["text"]
    s2_cer, s2_cer_info = _cer(ground_truth_text, s2_text)
    s2_wer, s2_wer_info = _wer(ground_truth_text, s2_text)
    recovery = error_recovery_rate(s1_cer, s2_cer)

    # ── Stage 3: Summarization ────────────────────────────────────────────
    summ = extractive_summarize(s2_text)
    s3_text = summ["text"]
    rouge = compute_rouge(ground_truth_summary or ground_truth_text, s3_text)
    # CER/WER of summary vs ground truth summary (if available)
    gt_summ = ground_truth_summary or ground_truth_text
    s3_cer, _ = _cer(gt_summ, s3_text)
    s3_wer, _ = _wer(gt_summ, s3_text)

    # ── Stage 4: Topic Classification ─────────────────────────────────────
    topic = classify_topic(s2_text)
    topic_correct = (
        int(topic["predicted_topic"].lower() == ground_truth_topic.lower())
        if ground_truth_topic else None
    )

    total_time = round(time.time() - t0, 3)

    # ── Snowball cascade: CER at each stage ───────────────────────────────
    snowball = {
        "baseline":         {"cer": 0.0, "wer": 0.0},
        "ocr":              {"cer": round(s1_cer, 2), "wer": round(s1_wer, 2)},
        "spell_correction": {"cer": round(s2_cer, 2), "wer": round(s2_wer, 2)},
        "summarization":    {"cer": round(s3_cer, 2), "wer": round(s3_wer, 2)},
    }
    # Snowball factor = ratio of final error to initial error
    if s1_cer > 0:
        snowball["amplification_factor"] = round(s3_cer / s1_cer, 2)
    else:
        snowball["amplification_factor"] = 1.0

    return {
        "error_rate": error_rate,
        "method": method,
        "total_time_s": total_time,
        "snowball": snowball,
        "stages": {
            "ocr": {
                "text": stage1_text,
                "cer": s1_cer, "wer": s1_wer,
                "method": method,
            },
            "spell_correction": {
                "text": s2_text,
                "cer": s2_cer, "wer": s2_wer,
                "recovery_pct": recovery,
                "corrections_made": sc["corrections_made"],
            },
            "summarization": {
                "text": s3_text,
                "cer": s3_cer, "wer": s3_wer,
                "rouge_1": rouge["rouge_1"],
                "rouge_2": rouge["rouge_2"],
                "rouge_l": rouge["rouge_l"],
                "num_input_sentences": summ["num_input_sentences"],
                "num_output_sentences": summ["num_output_sentences"],
            },
            "classification": {
                "predicted_topic": topic["predicted_topic"],
                "confidence": topic["confidence"],
                "topic_correct": topic_correct,
                "all_scores": topic["all_scores"],
                "all_confidences": topic["all_confidences"],
            },
        },
    }
