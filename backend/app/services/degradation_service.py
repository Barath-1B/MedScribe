"""
Degradation service — loads pre-computed ClinBERT study data and aggregates.
Ported from dashboard.py load_clinbert_data() + Tab 3 aggregation logic.
"""

from pathlib import Path
from functools import lru_cache

import pandas as pd

_PROJECT_ROOT = Path(__file__).parents[3]
CLINBERT_CSV = (
    _PROJECT_ROOT / "clinbert-error-propagation"
    / "clinbert-error-propagation" / "results" / "full_results.csv"
)


@lru_cache(maxsize=1)
def load_clinbert_data() -> pd.DataFrame | None:
    """Load the pre-computed degradation study CSV."""
    if not CLINBERT_CSV.exists():
        return None
    df = pd.read_csv(CLINBERT_CSV)
    df["error_pct"] = (df["error_rate"] * 100).round(0).astype(int)
    return df


def get_degradation_data() -> dict | None:
    """Return raw + aggregated degradation data as JSON-serialisable dict."""
    df = load_clinbert_data()
    if df is None:
        return None

    error_rates = sorted(df["error_pct"].unique().tolist())

    # Aggregate by stage
    ocr_agg = (df[df["stage_name"] == "ocr"]
               .groupby("error_pct")[["cer", "wer"]].mean().reset_index())
    spell_agg = (df[df["stage_name"] == "spell_correction"]
                 .groupby("error_pct")[["cer", "wer", "error_recovery_rate"]].mean().reset_index())
    summ_agg = (df[df["stage_name"] == "summarization"]
                .groupby("error_pct")[["rouge_1", "rouge_2", "rouge_l"]].mean().reset_index())
    cls_agg = (df[df["stage_name"] == "classification"]
               .groupby("error_pct")[["topic_correct", "topic_confidence"]].mean().reset_index())

    # Scale to percentages
    for col in ["cer", "wer"]:
        ocr_agg[col] = (ocr_agg[col] * 100).round(2)
        spell_agg[col] = (spell_agg[col] * 100).round(2)
    spell_agg["error_recovery_rate"] = (spell_agg["error_recovery_rate"] * 100).round(2)
    for col in ["rouge_1", "rouge_2", "rouge_l"]:
        summ_agg[col] = (summ_agg[col] * 100).round(2)
    cls_agg["topic_correct"] = (cls_agg["topic_correct"] * 100).round(2)
    cls_agg["topic_confidence"] = (cls_agg["topic_confidence"] * 100).round(2)

    return {
        "error_rates": error_rates,
        "aggregated": {
            "ocr":               ocr_agg.to_dict(orient="records"),
            "spell_correction":  spell_agg.to_dict(orient="records"),
            "summarization":     summ_agg.to_dict(orient="records"),
            "classification":    cls_agg.to_dict(orient="records"),
        },
    }
