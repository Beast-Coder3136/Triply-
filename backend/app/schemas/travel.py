

class TravelQueryRequest(BaseModel):
    message: str
    thread_id: str | None = None