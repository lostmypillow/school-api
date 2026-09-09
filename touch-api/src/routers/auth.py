"""補位學生登入.

請參考 `src.routers` 模組來了解如何重構


"""
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException

from src.database.exec_sql import exec_sql
from src.lib import deps, get_class_with_seats

logger = logging.getLogger("rich")
from src.models import AuthRequest, AuthResponse, ErrorResponse, RateableEmployee

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
    """確認學生是否可補位.

    請參考 `src.routers` 模組來了解如何重構.

    以下為本函式邏輯流程:

    1. 檢查該學生是否存在於資料庫中.
    2. 若用途為獎勵查詢:
        - 則直接回傳, 因為前端之後會另外查詢獎勵資訊.(是否能改善?例如現在就查詢獎勵, 或在改寫成 service 之後, 讓 IdentityService 呼叫 AwardsService, 以便這個 endpoint 能回傳更細緻的錯誤訊息.)
    3. 若用途為座位查詢:
        1. 檢查是否有可補位的班級, 若無則立刻回傳例外; 若有則繼續.
        2. 取得該學生目前的所有課程, 若這些課程中沒有包含目前有座位的班級, 則回傳例外; 否則繼續.
        3. 檢查該學生是否已經選過座位, 若有則回傳例外; 否則繼續.(若通過此檢查, 則會直接跳至回傳 AuthResponse)
    4. 若用途為評分員工:
        1. 取得今日所有值班員工
        2. 取得該學生已評分的員工
        3. 從今日值班員工中移除已評分者, 並將其附加至回傳資料中
    5. 回傳結果(若先前未提前回傳)

    Parameters
    ----------
    auth_request : AuthRequest
        請見 `src.models.auth_request`.

    Returns
    -------
    AuthResponse
        請見 `src.models.auth_response`.

    Raises
    ------
    HTTPException
        補位機會顯示的錯誤訊息

    .. todo:: - 解決此處顯示的 Ruff 錯誤
        - 將此邏輯移至獨立的 service 檔案中
    *由 林家民 於 2025/7/23 撰寫, 原文為自己寫的英文, 由 ChatGPT 翻譯為繁體中文。*
    """ # noqa: E501
    global settings
    try:
        student_details: dict[str, str] = await exec_sql(
            "one", "student_details", card_id=auth_request.student_id,
        )
        # print(student_details)
    # Example student_details value:
    # {
    #     "學號": "",
    #     "姓名": "",
    #     "性別": "男"
    # }
    except Exception:
        logger.exception(
            f"[AUTH {auth_request.student_id}] DB query student_details failed, raising Error 500",
        )
        raise HTTPException(500, detail="抱歉, 系統發生錯誤, 請洽導師! Error 001")

    if student_details is None or student_details == {}:
        logger.error(
            f"[AUTH {auth_request.student_id}] No student found, raising Error 404",
        )
        raise HTTPException(404, detail="抱歉, 查無此人!")

    auth_response = AuthResponse(**student_details)

    if auth_request.type == "awards":

        return auth_response

    if auth_request.type == "seat":

        try:
            class_with_seat = (await get_class_with_seats())["class_with_seats"]
        except Exception:
            logger.exception(
                f"[AUTH {auth_request.student_id}] Error calling get_class_with_seats(), raising Error 500",
            )
            raise HTTPException(500, detail="抱歉, 系統發生錯誤, 請洽導師! Error 003")

        if class_with_seat == {}:
            raise HTTPException(404, "抱歉, 目前沒有補位資料!")

        try:
            courses_of_student: list[dict[str, str]] = await exec_sql(
                "all", "student_match_course", student_id=auth_request.student_id,
            )

        # Example courses_of_student value:
        # [
        #     {
        #         "班別": ""
        #     }
        # ]
        except Exception:
            logger.exception(
                f"[AUTH {auth_request.student_id}] DB query student_match_course failed, raising Error 500",
            )
            raise HTTPException(500, detail="抱歉, 系統發生錯誤, 請洽導師! Error 002")

        if courses_of_student is None or courses_of_student == []:
            logger.error(
                f"[AUTH {auth_request.student_id}] No courses for {auth_request.student_id} found, raising Error 404",
            )
            raise HTTPException(404, detail="抱歉, 您沒有任何可補位之課程, 請洽導師!")

        try:
            assert isinstance(courses_of_student, list)
            assert isinstance(class_with_seat, dict)

            matches_course = any(
                isinstance(d, dict)
                and "班別" in d
                and d["班別"] == class_with_seat["班別"]
                for d in courses_of_student
            )
        except AssertionError:
            logger.error(f"[AUTH {auth_request.student_id}] Data structure issue")
            raise HTTPException(500, "抱歉, 系統發生錯誤, 請洽導師! Error 004")

        except KeyError as e:
            logger.exception(f"[AUTH {auth_request.student_id}] Missing key: {e}")
            raise HTTPException(500, "抱歉, 系統發生錯誤, 請洽導師! Error 005")

        except Exception as e:
            logger.exception(f"[AUTH {auth_request.student_id}] Unknown error: {e}")
            raise HTTPException(500, "抱歉, 系統發生錯誤, 請洽導師! Error 006")

        if matches_course == False:
            logger.error(
                f"[AUTH {auth_request.student_id}] Student s courses does NOT match course for seat",
            )
            raise HTTPException(404, detail="抱歉, 目前沒有您可選的補位資料, 請洽導師!")

        try:
            check_already_selected: list = await exec_sql(
                "all",
                "student_already_selected",
                course_id=class_with_seat["主檔號"],
                student_id=auth_request.student_id,
            )
        except Exception:
            logger.exception(
                f"[AUTH {auth_request.student_id}] DB query student_already_selected failed, raising Error 500",
            )
            raise HTTPException(500, detail="系統發生錯誤, 請洽導師! Error 007")
        # OUTPUT:
        # [
        #     {
        #         "sn": ,
        #         "主檔號": 4,
        #         "座位號": "A17",
        #         "學號": "",
        #         "登記時間": "2025-01-06T21:23:57.437000"
        #     }
        # ]
        current_class_with_seats = (await get_class_with_seats())["class_with_seats"]
        if (
            matches_course is False
            or check_already_selected != []
            or len(current_class_with_seats[
                auth_response.性別 + "座位"
            ])
            == 0
        ):

            logger.error(f"[AUTH {auth_request.student_id}] 目前沒有您可選的補位資料!")

            raise HTTPException(404, "目前沒有您可選的補位資料!")

    elif auth_request.type == "survey":

        try:
            emp_working_today = await exec_sql(
                "all",
                "student_today_employees",
                current_date=datetime.now().strftime("%Y-%m-%d"),
            )
        except Exception as e:
            logger.exception(f"[AUTH {auth_request.student_id}] Unknown error: {e}")
            raise HTTPException(500, "抱歉, 系統發生錯誤, 請洽導師! Error 008")

        if emp_working_today == []:
            raise HTTPException(404, "目前沒有可評分的員工!")

        for employee in emp_working_today:

            if "學號" in employee:

                employee["學號"] = employee["學號"].strip()

            if "主要部門" in employee:

                employee["主要部門"] = next(
                    (k for k, v in deps.items() if v == employee["主要部門"]), None,
                )

        try:
            voted_emp_week = await exec_sql(
                "all",
                "student_voted_employees",
                monday=(
                    datetime.now() - timedelta(days=datetime.now().weekday())
                ).strftime("%Y-%m-%d 00:00:00.000"),
                student_id=auth_request.student_id,
            )
        except Exception as e:
            logger.exception(f"[AUTH {auth_request.student_id}] Unknown error: {e}")
            raise HTTPException(500, "抱歉, 系統發生錯誤, 請洽導師! Error 009")

        rateable_employees = [
            RateableEmployee(**employee)
            for employee in emp_working_today
            if employee["學號"]
            not in [voted_emps["評分對象"] for voted_emps in voted_emp_week]
        ]

        if rateable_employees == []:

            raise HTTPException(404, "目前沒有可評分的員工!")

        auth_response.rateable_employees = rateable_employees

    return auth_response
