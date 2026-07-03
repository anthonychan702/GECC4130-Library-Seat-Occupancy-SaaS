from datetime import datetime
from pydantic import BaseModel


class PredictedOccupancyResponse(BaseModel):
    library_name: str
    next_period: str
    predicted_occupancy: int
    predicted_peak: str
    last_updated: datetime