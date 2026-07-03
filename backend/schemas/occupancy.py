from datetime import datetime
from pydantic import BaseModel


class OccupancyResponse(BaseModel):
    library_name: str
    current_occupancy: int
    last_updated: datetime