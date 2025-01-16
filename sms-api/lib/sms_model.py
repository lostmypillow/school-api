from pydantic import BaseModel
from typing import Any


class SMSModel(BaseModel):

    # 學號
    student_id: str

    # 對象
    recipient: str

    # 手機
    phone_number: str

    # 手機
    message_content: str

    # 預約時間
    send_time: Any
