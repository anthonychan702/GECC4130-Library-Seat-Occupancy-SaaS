from datetime import datetime, timezone
from backend.data_structure import OccupancyStore, ForecastPoint

# mock data
def get_predicted_occupancy_data():
    return {
        "library_name": "CUHK CC Library",
        "next_period": "4pm",
        "predicted_occupancy": 127,
        "predicted_peak": "2pm",
        "last_updated": datetime.now(timezone.utc)
    }