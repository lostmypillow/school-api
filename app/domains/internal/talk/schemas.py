from pydantic import BaseModel


class SendMessageRequest(BaseModel):
    sender: str
    recipient: str
    message: str
    password: str

class SendMessageResponse(BaseModel):
    success: bool
    detail: str
    result: dict | None = None
