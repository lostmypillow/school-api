# TODO:ADD DOCSTRING
import logging

from fastapi import APIRouter, HTTPException

logger = logging.getLogger("rich")
from src.database.exec_sql import exec_sql
from src.models.error_response import ErrorResponse
from src.models.seat_info import SeatInfo
from src.models.success_message import SuccessMessage

router = APIRouter(
    prefix="/seat",
    tags=["Seat"],
)

@router.post("/",
                  summary="Register a seat for student",
                  response_model=SuccessMessage,
                  responses={
                      200: {
                          "description": "Seat registration successful",
                          "model": SuccessMessage,
                      },
                      500: {
                          "model": ErrorResponse,
                          "description": "Internal server error",

                      },
                  })
async def register_seat(seat_info: SeatInfo):
    """
    Registers a seat number for the student.

    Parameters
    ----------
    seat_info : SeatInfo
        The seat info including student ID and seat serial number.
    """
    try:
        await exec_sql(
            "commit",
            "register_seat",
            student_id=seat_info.學號,
            sn=seat_info.號碼,
        )
        return SuccessMessage(message="success")
    except Exception as e:
        logger.exception(
            f"[SEAT ERROR] 學號={seat_info.學號}, 號碼={seat_info.號碼} - {e}")
        raise HTTPException(status_code=500, detail="抱歉，系統發生錯誤，請洽導師! Error 010")
