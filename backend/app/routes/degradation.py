"""Routes for the ClinBERT degradation study data."""

from fastapi import APIRouter, HTTPException

from app.services.degradation_service import get_degradation_data

router = APIRouter(prefix="/api/degradation", tags=["degradation"])


@router.get("")
def get_degradation():
    """Return aggregated degradation study data (error rates vs metrics)."""
    data = get_degradation_data()
    if data is None:
        raise HTTPException(404, "full_results.csv not found")
    return data
