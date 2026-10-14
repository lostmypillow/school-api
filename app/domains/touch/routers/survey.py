"""提交員工評分.

.. todo:: - 這裡的 `logger` 應改為 `` refactor branch 的 `Log`
"""

import logging

from fastapi import APIRouter, HTTPException

from app.core.exec_mssql_async import exec_mssql_async

from app.domains.touch.models.error_response import ErrorResponse
from app.domains.touch.models.success_message import SuccessMessage
from app.domains.touch.models.survey_info import SurveyInfo

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/survey",
    tags=["Survey"],
)
deps: dict = {
    "教務處": 2,
    "學務處": 4,
    "總務處": 8,
    "研發處": 9,
    "圖書館": 11,
}


@router.post(
    "/",
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
    },
)
async def rate_employee(survey_info: SurveyInfo):
    global deps
    try:
        await exec_mssql_async(
            "rate_employee",
            survey_info.student_id,
            deps[survey_info.employee_dep],
            survey_info.employee_id,
            survey_info.rating,
            fetch=False
        )
        return SuccessMessage(message="success")
    except KeyError as e:
        logger.error(f"[RATE ERROR] Invalid department: {survey_info.employee_dep} - {e}")
        raise HTTPException(status_code=400, detail="部門資訊有誤!")

    except Exception as e:
        logger.exception(f"[RATE ERROR] Failed to rate employee: {e}")
        raise HTTPException(status_code=500, detail="抱歉，系統發生錯誤，請洽導師!")
