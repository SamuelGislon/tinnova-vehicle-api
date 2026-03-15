from pydantic import BaseModel


class HealthLiveResponse(BaseModel):
    status: str


class HealthReadyResponse(BaseModel):
    status: str
    database: str
    redis: str


class SimpleMessageResponse(BaseModel):
    message: str
