from fastapi import APIRouter, Header, HTTPException, status, Response, Depends
from pydantic import BaseModel, Field
from datetime import datetime, time, timedelta
from typing import Optional
import os

from sqlalchemy.orm import Session
from ..db.db import get_db, OccupancyReading, EnvironmentalReading
from sqlalchemy.dialects.postgresql import insert


router = APIRouter(prefix = "/api")


# cookie
class PreferenceIn(BaseModel):
    study_preference: str
    preferred_floor: str



@router.post("/preferences")
def save_preferences(data: PreferenceIn, response: Response):
    # can save to database for building recommended zone model (db.save(data.model_dump())

    cookie_value = f"{data.study_preference}|{data.preferred_floor} "

    print(cookie_value)

    response.set_cookie(            # to tell frontend browser auto add cookie header next time and create cookie
        key = "cc_pref",              # header Cookie: cc_pref=Quiet zone|2F
        value = cookie_value,
        max_age=60 * 60 * 24 * 180,
        path="/",
        samesite="lax",
        secure=False,  
        httponly=False
    )

    return {
        "status": "ok",
        "saved": True,
        "preference": {
            "study_preference": data.study_preference,
            "preferred_floor": data.preferred_floor
        }
    }




from datetime import datetime
from zoneinfo import ZoneInfo

HKT = ZoneInfo("Asia/Hong_Kong")



# sensors payload

class OccupancyReadingCreate(BaseModel):
    signal: int


class EnvironmentalReadingCreate(BaseModel):
    zone: str = Field(min_length=1, max_length=26)
    temperature_c: Optional[float] = Field(default=None, ge=-20, le=60)
    humidity: Optional[float] = Field(default=None, ge=0, le=100)
    noise_db: Optional[float] = Field(default=None, ge=0, le=150)



SENSOR_API_KEY = os.getenv("SENSOR_API_KEY")


def verify_sensor_key(x_sensor_key: str | None) -> None:
    print(x_sensor_key)
    print(SENSOR_API_KEY)
    if x_sensor_key != SENSOR_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid sensor API key",
        )


now = datetime.now(HKT)
hour_str = now.strftime("%Y-%m-%d_%H")
print(hour_str)



# sensor signal: 
# 1 => +1 people
# 0 => -1 people







# example
# headers: {x-sensor-key: ABCDEFG12345}
# body: 
# {
#   "signal": 0 or 1,
# }









# for sensors to pass occupancy data
@router.post("/sensor/occupancy")
def create_occupancy_reading(sensor: OccupancyReadingCreate, x_sensor_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    verify_sensor_key(x_sensor_key)

    now = datetime.now(HKT)
    if not time(8, 20) < now.time() < time(22, 0):
        print("CC library is still not opened yet")
        return {"message": "CC library is not opened yet",}

    hour_str = now.strftime("%Y-%m-%d_%H")
    row = db.query(OccupancyReading).filter(OccupancyReading.hour_str == hour_str).first()

    prev = now - timedelta(hours=1)
    while (row is None and prev.time() > time(7, 00)):
        i = prev.strftime("%Y-%m-%d_%H")
        row = db.query(OccupancyReading).filter(OccupancyReading.hour_str == i).first()
        prev -= timedelta(hours=1)

    current_occupancy = 0 if row is None else row.occupant_count

    if sensor.signal == 1:
        current_occupancy += 1
    elif sensor.signal == 0:
        current_occupancy -= 1


    current_occupancy = 0 if current_occupancy < 0 else current_occupancy



    stmt = insert(OccupancyReading).values(
        hour_str = hour_str,
        occupant_count = current_occupancy,
        updated_at = now,
    )

    stmt = stmt.on_conflict_do_update(
        index_elements=[OccupancyReading.hour_str],
        set_={
            "occupant_count": stmt.excluded.occupant_count,
            "updated_at": stmt.excluded.updated_at,
        },
    )

    db.execute(stmt)
    db.commit()

    x = "+1" if sensor.signal == 1 else "-1"
    return {
        "message": "Occupancy reading received",
        "current_occupancy": current_occupancy,
        "received_data": sensor.signal,
        "occupancy": x,
        "received_at": now,
    }








# example
# headers: {x-sensor-key: ABCDEFG12345}
# body:
# {
#   "zone": "2F_study1" or "1F_hub3" or "G_pc2",
#   "temperature_c": 25,
#   "humidity": 0.79,
#   "noise_db": 30,
# }



# for sensors to pass environmantal data
@router.post("/sensor/environmental-data")
def create_environment_reading(sensor: EnvironmentalReadingCreate, x_sensor_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    verify_sensor_key(x_sensor_key)

    now = datetime.now(HKT)
    sensor.humidity *= 100

    type = sensor.zone.split("_")[1].rstrip("0123456789")


    if type == "study":
        type = "Quiet Study zone"
    elif type == "pc": 
        type = "PC zone"
    elif type == "overview":
        type = "Floor Overview"


    stmt = insert(EnvironmentalReading).values(
        zone= sensor.zone,
        zone_type= type,
        temperature_c= sensor.temperature_c,
        noise_db= sensor.noise_db,
        humidity_percent= sensor.humidity,
        updated_at= now,
    )

    stmt = stmt.on_conflict_do_update(
        index_elements=[EnvironmentalReading.zone],
        set_={
            "zone_type": type,
            "temperature_c": sensor.temperature_c,
            "noise_db": sensor.noise_db,
            "humidity_percent": sensor.humidity,
            "updated_at": stmt.excluded.updated_at,
        },
    )


    db.execute(stmt)
    db.commit()

    return {
        "message": "Environmental data received",
    }
