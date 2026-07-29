# backend/routers/occupancy.py
from fastapi import APIRouter
router = APIRouter(prefix="/occupancy", tags=["occupancy"])

from backend.schemas.occupancy import OccupancyResponse
from backend.services.occupancy_service import get_current_occupancy_data

from ..db.db import get_db, OccupancyReading
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

@router.get("/current", response_model = OccupancyResponse)
def get_current_occupancy(db: Session = Depends(get_db)):
    return get_current_occupancy_data(db, OccupancyReading)