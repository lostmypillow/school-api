"""補位學生補位.


"""
import logging

from fastapi import APIRouter, HTTPException

from app.core.exec_mssql_async import exec_mssql_async
from app.domains.touch.schemas.error_response import ErrorResponse
from app.domains.touch.schemas.seat_info import SeatInfo
from app.domains.touch.schemas.success_message import SuccessMessage

logger = logging.getLogger("__name__")
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
    try:
        await exec_mssql_async(
            "register_seat",
            seat_info.student_id,
            seat_info.seat_number,
            fetch=False
        )
        return SuccessMessage(message="success")
    except Exception as e:
        logger.exception(
            msg=f"[SEAT ERROR] student_id={seat_info.student_id}, 號碼={seat_info.seat_number} - {e}", exc_info=e)
        raise HTTPException(status_code=500, detail="抱歉，系統發生錯誤，請洽導師! Error 010")
