"""補位學生補位.


"""
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
    """為學生註冊補位.

    Parameters
    ----------
    seat_info : SeatInfo
        包含學生 ID 與座位序號的資訊. 詳情請見 `src.models.seat_info`.

    .. todo:: - 解決此處顯示的 Ruff 錯誤
        - 將此邏輯移至獨立的 service 檔案中
    *由 林家民 於 2025/7/23 撰寫, 原文為自己寫的英文, 由 ChatGPT 翻譯為繁體中文。*
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
