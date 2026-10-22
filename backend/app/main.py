from fastapi import FastAPI 
from routes.travel import travel_router
# This is to allow nested event loops for async calls in FastAPI
import nest_asyncio
nest_asyncio.apply()

app = FastAPI()
app.include_router(travel_router)

