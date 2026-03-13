from pydantic import BaseModel


class VideoInfoResponse(BaseModel):
    title: str
    channel: str
    owner: str
    filmstrip_60_url: str
    embed_url: str

class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
