from datetime import datetime, timezone
from backend.data_structure import OccupancyStore, ForecastPoint
from backend.model.forecast import forecast_today_response

# services determine the response data logic


def get_predicted_occupancy_data():

    series = forecast_today_response()

    # return {
    #     "library_name": "CUHK CC Library",
    #     "series": series,
    #     "last_updated": datetime.now(timezone.utc)
    # }


    # Mock data
    return {
        "library_name": "CUHK CC Library",
        "next_period": "4pm",
        "predicted_occupancy": 127,
        "predicted_peak": "2pm",
        "last_updated": datetime.now(timezone.utc)
    }
