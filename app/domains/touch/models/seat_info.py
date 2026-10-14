"""一個座位的資訊.


"""
from pydantic import BaseModel


class SeatInfo(BaseModel):  # noqa: D101
    student_id: str
    seat_number: int
