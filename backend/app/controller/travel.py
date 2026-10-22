import traceback
from fastapi.responses import JSONResponse
from agents.graph import run_travel_agent , resume_travel_agent
from pydantic import BaseModel , Field 


class TravelQueryRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ApprovalRequest(BaseModel):
    thread_id : str  = Field(... , min_length=1)
    approved : bool = Field(...)
    feedback : str = Field(description="User Feedback of the generated plan")



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


async def approve_travel_plan(body : ApprovalRequest):
    try:
        if not body.approved and not body.feedback.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Please provide revision feedback when rejecting the draft.",
                },
            )

        result = resume_travel_agent(
            thread_id=body.thread_id,
            approved=body.approved,
            feedback=body.feedback,
        )

        return JSONResponse(
            content={
                "success": True,
                **result,
            }
        )

    except Exception as exc:
        print("APPROVAL ERROR:", exc)
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
            },
        )
