"""Routes for the degradation/snowball study data."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.degradation_service import get_degradation_data

router = APIRouter(prefix="/api/degradation", tags=["degradation"])


@router.get("")
def get_degradation(db: Session = Depends(get_db)):
    """Return aggregated degradation data from experiments."""
    return get_degradation_data(db)
