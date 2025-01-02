from pydantic import BaseModel
from typing import Any, AnyStr
class Message(BaseModel):
    type: AnyStr
    data: Any