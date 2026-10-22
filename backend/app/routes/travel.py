
from fastapi import APIRouter
from controller.travel import plan_travel_trip , TravelQueryRequest , approve_travel_plan , ApprovalRequest

travel_router = APIRouter(prefix="/travel")

@travel_router.post("/plan")
async def plan_travel(body : TravelQueryRequest):
  return  await plan_travel_trip(body)

@travel_router.post("/plan/approve")
async def approve_travel( body : ApprovalRequest ):
  return await approve_travel_plan(body)