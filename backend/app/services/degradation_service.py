"""
Degradation service — computes snowball degradation from experiment results.
Shows how OCR errors cascade through each pipeline stage.
"""

from collections import defaultdict
from sqlalchemy.orm import Session

from app.models import Experiment


def get_degradation_data(db: Session) -> dict:
    """
    Build degradation curves from completed experiments.
    Groups by error_rate and stage, computing mean metrics at each point.
    Returns flat aggregated list that the frontend can consume directly.
    """
    experiments = (
        db.query(Experiment)
        .filter(Experiment.status == "completed")
        .all()
    )

    if not experiments:
        return {"aggregated": [], "error_rates": [], "total_experiments": 0}

    # Collect all stage results grouped by (error_rate, stage_name)
    buckets = defaultdict(lambda: defaultdict(list))

    for exp in experiments:
        rate = exp.error_rate
        for sr in exp.stage_results:
            buckets[rate][sr.stage_name].append(sr)

    aggregated = []
    error_rates = sorted(buckets.keys())

    for rate in error_rates:
        for stage_name in ["ocr", "spell_correction", "summarization", "classification"]:
            results = buckets[rate].get(stage_name, [])
            if not results:
                continue

            row = {
                "error_rate": rate,
                "stage": stage_name,
                "n_runs": len(results),
            }

            # CER/WER for ocr and spell_correction stages
            cers = [r.cer for r in results if r.cer is not None]
            wers = [r.wer for r in results if r.wer is not None]
            if cers:
                row["mean_cer"] = round(sum(cers) / len(cers), 2)
            if wers:
                row["mean_wer"] = round(sum(wers) / len(wers), 2)

            # Recovery rate for spell_correction
            recoveries = [r.error_recovery_rate for r in results if r.error_recovery_rate is not None]
            if recoveries:
                row["mean_recovery"] = round(sum(recoveries) / len(recoveries), 2)

            # ROUGE for summarization
            r1s = [r.rouge_1 for r in results if r.rouge_1 is not None]
            r2s = [r.rouge_2 for r in results if r.rouge_2 is not None]
            rls = [r.rouge_l for r in results if r.rouge_l is not None]
            if r1s:
                row["mean_rouge_1"] = round(sum(r1s) / len(r1s), 2)
                row["mean_rouge_2"] = round(sum(r2s) / len(r2s), 2)
                row["mean_rouge_l"] = round(sum(rls) / len(rls), 2)

            # Classification accuracy
            corrects = [r.topic_correct for r in results if r.topic_correct is not None]
            confs = [r.topic_confidence for r in results if r.topic_confidence is not None]
            if corrects:
                row["mean_accuracy"] = round(sum(corrects) / len(corrects) * 100, 2)
            if confs:
                row["mean_confidence"] = round(sum(confs) / len(confs), 4)

            aggregated.append(row)

    return {
        "aggregated": aggregated,
        "error_rates": error_rates,
        "total_experiments": len(experiments),
    }
