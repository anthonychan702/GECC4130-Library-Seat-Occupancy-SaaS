from datetime import datetime, timezone
from backend.data_structure import OccupancyStore, ForecastPoint

# mock data
def get_current_occupancy_data():
    return {
        "library_name": "CUHK CC Library",
        "current_occupancy": 215,
        "last_updated": datetime.now(timezone.utc),
    }