import random
import requests
from time import sleep

API_URL = "http://127.0.0.1:8000/api/sensor/environmental-data"
SENSOR_KEY = "ABCDEFG12345"

floors = {
    "second": {
        "overview": {"zone_id": "2F_overview", "type": "overview" },
        "zones": [
            {"id": "2F_hub1", "type": "reading"},
            {"id": "2F_study2", "type": "reading"},
            {"id": "2F_study3", "type": "reading"},
            {"id": "2F_study4", "type": "reading"},
            {"id": "2F_study6", "type": "reading"},
            {"id": "2F_study5", "type": "reading"},
            {"id": "2F_study7", "type": "reading"},
            {"id": "2F_study8", "type": "reading"},
            {"id": "2F_study9", "type": "reading"},
            {"id": "2F_pc10", "type": "computing"},
        ],
    },
    "first": {
        "overview": {"zone_id": "1F_overview", "type": "overview" },
        "zones": [
            {"id": "1F_study1", "type": "reading"},
            {"id": "1F_study2", "type": "reading"},
            {"id": "1F_study3", "type": "reading"},
            {"id": "1F_study4", "type": "reading"},
            {"id": "1F_study6", "type": "reading"},
            {"id": "1F_study5", "type": "reading"},
            {"id": "1F_study10", "type": "reading"},
            {"id": "1F_study7", "type": "reading"},
            {"id": "1F_hub8", "type": "reading"},
            {"id": "1F_study9", "type": "reading"},
            {"id": "1F_study11", "type": "reading"},
            {"id": "1F_study12", "type": "reading"},
            {"id": "1F_pc13", "type": "computing"},
        ],
    },
    "ground": {
        "overview": {"zone_id": "GF_overview", "type": "overview" },
        "zones": [
            {"id": "GF_study5", "type": "reading"},
            {"id": "GF_study9", "type": "reading"},
            {"id": "GF_study2", "type": "reading"},
            {"id": "GF_study6", "type": "reading"},
            {"id": "GF_study7", "type": "reading"},
            {"id": "GF_pc8", "type": "computing"},
            {"id": "GF_pc3", "type": "computing"},
            {"id": "GF_study4", "type": "reading"},
            {"id": "GF_study1", "type": "reading"},
        ],
    },
    "lower_ground": {
        "overview": {"zone_id": "LG_overview", "type": "overview" },
        "zones": [],
    },
}

headers = {
    "x-sensor-key": SENSOR_KEY,
    "Content-Type": "application/json",
}


def random_payload(zone_id: str, zone_type: str = "reading"):
    if zone_id.endswith("_overview"):
        temp = round(random.uniform(23.5, 26.5), 1)
        humidity = round(random.uniform(0.50, 0.68), 2)
        noise = random.randint(32, 48)
    elif zone_type == "computing":
        temp = round(random.uniform(24.0, 27.5), 1)
        humidity = round(random.uniform(0.48, 0.65), 2)
        noise = random.randint(40, 58)
    else:
        temp = round(random.uniform(22.5, 26.0), 1)
        humidity = round(random.uniform(0.50, 0.72), 2)
        noise = random.randint(30, 45)

    return {
        "zone": zone_id,
        "temperature_c": temp,
        "humidity": humidity,
        "noise_db": noise,
    }


def post_one(payload):
    response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
    try:
        body = response.json()
    except Exception:
        body = response.text

    print(f"{response.status_code} | {payload['zone']} | {body}")


def seed_all():
    for floor in floors.values():
        overview_zone = floor["overview"]["zone_id"]
        post_one(random_payload(overview_zone, "overview"))
        sleep(0.05)

        for zone in floor["zones"]:
            post_one(random_payload(zone["id"], zone["type"]))
            sleep(0.05)


if __name__ == "__main__":
    seed_all()