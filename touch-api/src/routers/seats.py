from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from ..models.student_model import Student
from ..database import execute_SQL
from pydantic import BaseModel
from ..event_manager import send_event_to_clients
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from ..models.course_model import Course
import asyncio
router = APIRouter(
    prefix="/seats",
    tags=["Seats"],
)


class SeatModel(BaseModel):
    student_id: str
    sn: int


@router.post('/')
async def register_seat(seat_info: SeatModel):
    try:
        Student.register_seat(seat_info)
    except HTTPException as e:
        raise e
    await asyncio.create_task(send_event_to_clients(
        {
            "type": "remaining",
            "data": Course().model_dump()
        }
    ))
    return "ok"
