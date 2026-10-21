import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status

from app.core.exec_psql import exec_mssql_async
from app.domains.touch.lib import deps, get_class_with_seats
from app.domains.touch.schemas import AuthRequest, AuthResponse, ErrorResponse, RateableEmployee

logger = logging.getLogger("__name__")

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/",
    summary="學生身份驗證",
    description="根據學生 ID 與驗證種類進行身份驗證並回傳相關資訊",
    response_model=AuthResponse,
    responses={
        200: {"model": AuthResponse, "description": "Student authorized successfully"},
        404: {
            "model": ErrorResponse,
            "description": "Not found - student, data, or rating target missing",
        },
    },
)
async def authorize_student(auth_request: AuthRequest):
    try:
        student_details_result = await exec_mssql_async("student_details", auth_request.student_id)
        student_details: dict[str, str] = student_details_result[0]
    except Exception as e:
        logger.exception(
            msg=f"[AUTH {auth_request.student_id}] DB query student_details failed, raising Error 500", exc_info=e
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="抱歉, 系統發生錯誤, 請洽導師! Error 001")

    if student_details is None or student_details == {}:
        logger.error(
            f"[AUTH {auth_request.student_id}] No student found, raising Error 404",
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="抱歉, 查無此人!")

    auth_response: AuthResponse = AuthResponse.model_validate(student_details)

    if auth_request.type == "awards":

        return auth_response

    if auth_request.type == "seat":

        try:
            class_with_seat = (await get_class_with_seats())["class_with_seats"]
        except Exception:
            logger.exception(
                f"[AUTH {auth_request.student_id}] Error calling get_class_with_seats(), raising Error 500",
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="抱歉, 系統發生錯誤, 請洽導師! Error 003")

        if class_with_seat == {}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="抱歉, 目前沒有補位資料!")

        try:
            courses_of_student: list[dict[str, str]] = await exec_mssql_async( "student_match_course", auth_request.student_id,
            )

        except Exception:
            logger.exception(
                f"[AUTH {auth_request.student_id}] DB query student_match_course failed, raising Error 500",
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="抱歉, 系統發生錯誤, 請洽導師! Error 002")

        if courses_of_student is None or courses_of_student == []:
            logger.error(
                f"[AUTH {auth_request.student_id}] No courses for {auth_request.student_id} found, raising Error status.HTTP_404_NOT_FOUND",
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="抱歉, 您沒有任何可補位之課程, 請洽導師!")

        try:
            assert isinstance(courses_of_student, list)
            assert isinstance(class_with_seat, dict)

            matches_course = any(
                isinstance(d, dict)
                and "legacy_course_num" in d
                and d["legacy_course_num"] == class_with_seat["legacy_course_num"]
                for d in courses_of_student
            )
        except AssertionError:
            logger.error(f"[AUTH {auth_request.student_id}] Data structure issue")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="抱歉, 系統發生錯誤, 請洽導師! Error 004")

        except KeyError as e:
            logger.exception(f"[AUTH {auth_request.student_id}] Missing key: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="抱歉, 系統發生錯誤, 請洽導師! Error 005")

        except Exception as e:
            logger.exception(f"[AUTH {auth_request.student_id}] Unknown error: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="抱歉, 系統發生錯誤, 請洽導師! Error 006")

        if not matches_course:
            logger.error(
                f"[AUTH {auth_request.student_id}] Student s courses does NOT match course for seat",
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="抱歉, 目前沒有您可選的補位資料, 請洽導師!")

        try:
            check_already_selected: list = await exec_mssql_async(
                "student_already_selected", class_with_seat["file_no"], auth_request.student_id,
            )
        except Exception as e:
            logger.exception(
                msg=f"[AUTH {auth_request.student_id}] DB query student_already_selected failed, raising Error 500", exc_info=e
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="系統發生錯誤, 請洽導師! Error 007")
        # OUTPUT:
        # [
        #     {
        #         "sn": ,
        #         "file_no": 4,
        #         "seat_no": "A17",
        #         "student_id": "",
        #         "created_at": "2025-01-06T21:23:57.437000"
        #     }
        # ]
        current_class_with_seats = (await get_class_with_seats())["class_with_seats"]
        if (
            matches_course is False
            or check_already_selected != []
            or len(current_class_with_seats[
                auth_response.gender + "座位"
            ])
            == 0
        ):

            logger.error(f"[AUTH {auth_request.student_id}] 目前沒有您可選的補位資料!")

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目前沒有您可選的補位資料!")

    elif auth_request.type == "survey":

        try:
            emp_working_today = await exec_mssql_async(
                "student_today_employees",
                datetime.now().strftime("%Y-%m-%d"),
            )
        except Exception as e:
            logger.exception(f"[AUTH {auth_request.student_id}] Unknown error: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="抱歉, 系統發生錯誤, 請洽導師! Error 008")

        if not emp_working_today:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目前沒有可評分的員工!")

        for employee in emp_working_today:

            if "student_id" in employee:

                employee["student_id"] = employee["student_id"].strip()

            if "main_department" in employee:

                employee["main_department"] = next(
                    (k for k, v in deps.items() if v == employee["main_department"]), None,
                )

        try:
            voted_emp_week = await exec_mssql_async(
                "student_voted_employees",
                (
                    datetime.now() - timedelta(days=datetime.now().weekday())
                ).strftime("%Y-%m-%d 00:00:00.000"),auth_request.student_id,
            )
        except Exception as e:
            logger.exception(f"[AUTH {auth_request.student_id}] Unknown error: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="抱歉, 系統發生錯誤, 請洽導師! Error 009")

        rateable_employees = [
            RateableEmployee(**employee)
            for employee in emp_working_today
            if employee["student_id"]
            not in [voted_emps["subject"] for voted_emps in voted_emp_week]
        ]

        if not rateable_employees:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目前沒有可評分的員工!")

        auth_response.rateable_employees = rateable_employees

    return auth_response
