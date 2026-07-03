from fastapi import APIRouter, Response
from pydantic import BaseModel

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

