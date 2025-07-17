"""一個座位的資訊.


"""
from pydantic import BaseModel


class SeatInfo(BaseModel):  # noqa: D101
    學號: str
    號碼: int
