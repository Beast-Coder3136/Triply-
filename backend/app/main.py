from fastapi import FastAPI 
from routes.travel import query_router

app = FastAPI()
app.include_router(query_router)

