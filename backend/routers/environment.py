# backend/routers/occupancy.py
from fastapi import APIRouter, HTTPException,Depends
from ..db.db import get_db, EnvironmentalReading
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone, time
from datetime import datetime
from zoneinfo import ZoneInfo

router = APIRouter(prefix="/env", tags=["environment"])
HKT = ZoneInfo("Asia/Hong_Kong")

# for sensors to pass environment data
@router.get("/environmental-data")
def create_environment_reading(zone: str, db: Session = Depends(get_db)):

    row = db.query(EnvironmentalReading).filter(EnvironmentalReading.zone == zone).first()

    now = datetime.now(HKT)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No environmental data found for zone '{zone}'")

    return {
        "zone": row.zone,
        "zone_type": row.zone_type,
        "temperature_c": row.temperature_c,
        "noise_db": row.noise_db,
        "humidity_percent": row.humidity_percent,
        "last_updated": row.updated_at
    }
