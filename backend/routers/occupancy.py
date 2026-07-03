# backend/routers/occupancy.py

from fastapi import APIRouter
router = APIRouter(prefix="/occupancy", tags=["occupancy"])


from backend.schemas.occupancy import OccupancyResponse
from backend.services.occupancy_service import get_current_occupancy_data



@router.get("/current", response_model = OccupancyResponse)
def get_current_occupancy():
    return get_current_occupancy_data()