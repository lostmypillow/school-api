from pydantic import BaseModel, Field
from typing import Literal, Optional
class Device(BaseModel):
    device_id: Optional[int] = Field(None)
    teacher_id: Optional[int] = Field(None)