
from fastapi import APIRouter
from controller.travel import plan_travel_trip , TravelQueryRequest

query_router = APIRouter(prefix="/travel")

@query_router.post("/plan")
async def plan_travel(body : TravelQueryRequest):
  return  await plan_travel_trip(body)