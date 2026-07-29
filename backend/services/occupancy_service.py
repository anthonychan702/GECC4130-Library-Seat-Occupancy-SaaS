from datetime import datetime, timezone, time
from backend.data_structure import OccupancyStore, ForecastPoint
from zoneinfo import ZoneInfo


HKT = ZoneInfo("Asia/Hong_Kong")

def get_current_occupancy_data(db, OccupancyReading):

    row = db.query(OccupancyReading).order_by(OccupancyReading.updated_at.desc()).first()
    if not row or not row.hour_str:
        return {
            "library_name": "CUHK CC Library",
            "current_occupancy": 0,
            "last_updated": datetime.now(timezone.utc),
            "message": "Library is closed",
        }


    now = datetime.now(HKT)
    today = now.strftime("%Y-%m-%d")
    date = row.hour_str.split("_")[0] 

    current_occupancy = row.occupant_count if date == today else 0

    message = "Busy now" if current_occupancy > 100 else "Available"

    w = now.weekday()
    t = now.time()


    if w in (0, 1, 2, 3, 4) and not (time(8, 20) < t < time(22, 0)):
        current_occupancy = 0
        message = "Library is closed"
    elif w == 5 and not (time(8, 20) < t < time(19, 0)):
        current_occupancy = 0
        message = "Library is closed"
    elif w == 6 and not (time(11, 0) < t < time(19, 0)):
        current_occupancy = 0
        message = "Library is closed"

    return {
        "library_name": "CUHK CC Library",
        "current_occupancy": current_occupancy,
        "last_updated": datetime.now(timezone.utc),
        "message": message,
    }