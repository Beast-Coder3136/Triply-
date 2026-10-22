
from fastapi.responses import JSONResponse
from agents.graph import run_travel_agent
from pydantic import BaseModel

class TravelQueryRequest(BaseModel):
    message: str
    thread_id: str | None = None

async def plan_travel_trip(body : TravelQueryRequest ):
    try:
        user_message = body.message.strip()

        if not user_message:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Message cannot be empty."
                }
            )

        result = run_travel_agent(
            user_input=user_message,
            thread_id=body.thread_id
        )

        return result 

    except Exception as e:
        print("ERROR:", e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )
  