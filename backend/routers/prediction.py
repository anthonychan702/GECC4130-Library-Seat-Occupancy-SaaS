# backend/routers/prediction.py for time series forecast rout

from fastapi import APIRouter
router = APIRouter(prefix="/prediction", tags=["prediction"])

from backend.schemas.prediction import PredictedOccupancyResponse
from backend.services.prediction_service import get_predicted_occupancy_data


@router.get("/next-hour", response_model = PredictedOccupancyResponse)
def get_next_hour():
    return get_predicted_occupancy_data()