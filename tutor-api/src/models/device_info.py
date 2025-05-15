from typing import Optional, List
from pydantic import BaseModel, Field

class DeviceInfo(BaseModel):
    device_id: int = Field(..., alias="設備號碼")
    teacher_id: Optional[str] = Field(None, alias="老師編號")

# If you're receiving a list of these: