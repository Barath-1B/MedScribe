"""Routes for full 4-stage pipeline results on dataset-1."""

from fastapi import APIRouter
import numpy as np

from app.services.pipeline_service import get_pipeline_results

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.get("")
def get_pipeline():
    """Return full 4-stage pipeline results for all dataset-1 documents."""
    results = get_pipeline_results()

    if results:
        averages = {
            "s1_cer":        round(float(np.mean([r["s1_cer"] for r in results])), 2),
            "s2_cer":        round(float(np.mean([r["s2_cer"] for r in results])), 2),
            "s3_rouge1":     round(float(np.mean([r["s3_rouge1"] for r in results])), 2),
            "s4_confidence": round(float(np.mean([r["s4_confidence"] for r in results])), 4),
        }
    else:
        averages = {}

    return {"results": results, "averages": averages, "count": len(results)}
