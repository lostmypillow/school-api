"""提交員工評分.

.. todo:: - 這裡的 `logger` 應改為 `` 的 `Log`
"""
import logging

from fastapi import APIRouter, HTTPException

from src.database.exec_sql import exec_sql

logger = logging.getLogger("rich")
from src.models.error_response import ErrorResponse
from src.models.success_message import SuccessMessage
from src.models.survey_info import SurveyInfo

router = APIRouter(
    prefix="/survey",
    tags=["Survey"],
)
deps: dict = {
                : 2,
                "": 4,
                : 8,
                : 9,
                : 11,
            }
@router.post("/",
    summary="Submit a rating for an employee",
    response_model=SuccessMessage,
    responses={
        200: {
            "description": "Rating submitted successfully",
            "model": SuccessMessage,
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse,
        },
    })
async def rate_employee(survey_info: SurveyInfo):
    """將員工評分提交至資料庫.

    Parameters
    ----------
    survey_info : SurveyInfo
        請見 `src.models.survey_info`.

    Raises
    ------
    HTTPException
        錯誤訊息將顯示於補位機上.

    .. todo:: - 解決此處顯示的 Ruff 錯誤
        - 將此邏輯移至獨立的 service 檔案中
    *由 林家民 於 2025/7/23 撰寫, 原文為自己寫的英文, 由 ChatGPT 翻譯為繁體中文。*
    """
    global deps
    try:
        await exec_sql(
            "commit",
            "rate_employee",
            student_id=survey_info.student_id,
            department=deps[survey_info.employee_dep],
            employee_id=survey_info.employee_id,
            rating=survey_info.rating,
        )
        return SuccessMessage(message="success")
    except KeyError as e:
        logger.error(f"[RATE ERROR] Invalid department: {survey_info.employee_dep} - {e}")
        raise HTTPException(status_code=400, detail="部門資訊有誤!")

    except Exception as e:
        logger.exception(f"[RATE ERROR] Failed to rate employee: {e}")
        raise HTTPException(status_code=500, detail="抱歉，系統發生錯誤，請洽導師!")
