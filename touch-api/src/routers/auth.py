from fastapi import APIRouter, HTTPException
from typing import Literal
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from src.config import settings
from src.database.async_operations import exec_sql
from src.lib.custom_logger import logger
from src.lib.get_class_with_seats import get_class_with_seats
from src.lib.deps import deps

auth_router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


class AuthData(BaseModel):
    """_summary_

    Attributes
    ----------
    student_id : str

        Student ID

    type: Literal['seats', 'survey']

        Either 'seats' or 'survey'
    """
    student_id: str = Field(..., example="")
    type: Literal['seats', 'survey']


class RateableEmployee(BaseModel):
    學號: str = Field(..., example="000000")
    姓名: str = Field(..., example="王小明")
    主要部門: Literal[, , "", , ]


class AuthResponse(BaseModel):
    """_summary_

    Parameters
    ----------
    Attributes
    ----------
    學號: str

        Student ID

    姓名: str

        Self explanatory

    性別: str


    type: Literal['seats', 'survey']

        not to be confused with python types, either 'seats' or 'survey'
    """
    學號: str = Field(..., example="000000")
    姓名: str = Field(..., example="王小明")
    性別: Literal["男", "女"]
    rateable_employees: list[RateableEmployee] = Field(default_factory=list)


{
    "student_id": "",
    "course": "",
    "course_num": 4,
    "type": "survey"
}


class ErrorResponse(BaseModel):
    detail: str = Field(..., example="錯誤訊息")


@auth_router.post('/', response_model=AuthResponse,  responses={
    200: {"description": "Student authorized successfully"},
    400: {
        "model": ErrorResponse,
        "description": "Bad request"
    },
    403: {
        "model": ErrorResponse,
        "description": "Forbidden - not allowed to vote or select seat"
    },
    404: {
        "model": ErrorResponse,
        "description": "Not found - student, data, or rating target missing"
    },
    409: {
        "model": ErrorResponse,
        "description": "Conflict - seat already selected"
    },
})
async def authorize_student(auth_data: AuthData) -> AuthResponse:
    global settings
    """Authorize student and return appropriate data. See code at routers/auth.py

    Parameters
    ----------
    auth_data : AuthData
        See AuthData in Schemas section below

    Returns
    -------
    AuthResponse
        See AuthResponse in Responses section Code 200, or in Schemas section below.

    Raises
    ------
    HTTPException
        See router/auth.py for all HTTPException triggers.
    """
    try:
        student_details: dict[str, str] = await exec_sql(
            'one',
            'student_details',
            card_id=auth_data.student_id
        )
        print(student_details)
        # Example student_details value:
    # {
    #     "學號": "",
    #     "姓名": "",
    #     "性別": "男"
    # }
    except Exception as e:
        logger.exception(
            f'[AUTH {auth_data.student_id}] DB query student_details failed, raising Error 500')
        raise HTTPException(500, detail="抱歉，系統發生錯誤! Error code: 001")

    if student_details is None or student_details == {}:
        logger.error(
            f'[AUTH {auth_data.student_id}] No student found, raising Error 404')
        raise HTTPException(404, detail="抱歉，查無此人!")

    auth_response = AuthResponse(**student_details)

    if auth_data.type == "seats":

        try:
            class_with_seat = await get_class_with_seats()
        except Exception as e:
            logger.exception(
                f'[AUTH {auth_data.student_id}] Error calling get_class_with_seats(), raising Error 500')
            raise HTTPException(500, detail="抱歉，系統發生錯誤! Error code: 003")
        
        if class_with_seat == {}:
            raise HTTPException(404, "抱歉，目前沒有補位資料!")

        try:
            courses_of_student: list[dict[str, str]] = await exec_sql(
                'all',
                'student_match_course',
                student_id=auth_data.student_id
            )
            print(student_details)
            # Example student_details value:
        # [
        #     {
        #         "班別": ""
        #     }
        # ]
        except Exception as e:
            logger.exception(
                f'[AUTH {auth_data.student_id}] DB query student_match_course failed, raising Error 500')
            raise HTTPException(500, detail="抱歉，系統發生錯誤! Error code: 002")

        if courses_of_student is None or courses_of_student == []:
            logger.error(
                f'[AUTH {auth_data.student_id}] No courses for {auth_data.student_id} found, raising Error 404')
            raise HTTPException(404, detail="抱歉，您沒有任何課程!")

        try:
            assert isinstance(courses_of_student, list)
            assert isinstance(class_with_seat, dict)

            matches_course = any(
                isinstance(
                    d, dict) and '班別' in d and d['班別'] == class_with_seat.get('班別')
                for d in courses_of_student
            )
        except AssertionError:
            logger.error(f"[AUTH {auth_data.student_id}] Data structure issue")
            raise HTTPException(500, "抱歉，系統發生錯誤! Error code: 004")
        
        except KeyError as e:
            logger.exception(f"[AUTH {auth_data.student_id}] Missing key: {e}")
            raise HTTPException(500, "抱歉，系統發生錯誤! Error code: 005")
        
        except Exception as e:
            logger.exception(
                f"[AUTH {auth_data.student_id}] Unknown error: {e}")
            raise HTTPException(500, "抱歉，系統發生錯誤! Error code: 006")

        if matches_course == False:
            logger.error(
                f'[AUTH {auth_data.student_id}] Student s courses does NOT match course for seats')
            raise HTTPException(404, detail="抱歉，目前沒有您可選的補位資料!")
        try:
            check_already_selected: list = await exec_sql(
                'all',
                'student_already_selected',
                course_id=class_with_seat['主檔號'],
                student_id=auth_data.student_id
            )
            print(f"check_select: {check_already_selected}")
        except Exception as e:
            logger.exception(
                f'[AUTH {auth_data.student_id}] DB query student_already_selected failed, raising Error 500')
            raise HTTPException(500, detail="系統發生錯誤，error code: 007")
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

        # Technically, i should be doing the any() function like i did with match class.
        # But considering there's only one class for selection in a given day, and the SQL already checks for courses selected today, i just check if it's empty
        already_selected: bool = False if check_already_selected == [] else True

        logger.info(
            f'[AUTH {auth_data.student_id}] Student has already selected seat for course'
            if already_selected else
            f'[AUTH {auth_data.student_id}] Student has NOT already selected seat for course')

        if matches_course is False or already_selected is True:

            logger.error(f'[AUTH {auth_data.student_id}] 目前沒有您可選的補位資料')

            raise HTTPException(404, "目前沒有您可選的補位資料")

        else:

            logger.info(
                f'[AUTH {auth_data.student_id}] Success! Returned data!')

            return auth_response

    elif auth_data.type == "survey":

        logger.info(
            f'[AUTH {auth_data.student_id}] Student details exist and auth is for survey')

        if settings.DEBUG is True:
            logger.info('debug mode is on')
        else:
            logger.info('DEBUG mode is not on')
        emp_working_today = await exec_sql(
            'all',
            'student_today_employees',
            current_date=datetime.now().strftime('%Y-%m-%d')
        )
        # TODO replace debug values: datetime.now().strftime('%Y-%m-%d')'2020-09-16'

        for employee in emp_working_today:

            if "學號" in employee:

                employee['學號'] = employee['學號'].strip()

            if '主要部門' in employee:

                employee['主要部門'] = next((
                    k
                    for k, v in deps.items()
                    if v == employee['主要部門']),
                    None
                )

        voted_emp_week = await exec_sql(
            'all',
            'student_voted_employees',
            monday=(datetime.now() - timedelta(days=datetime.now().weekday())
                    ).strftime('%Y-%m-%d 00:00:00.000'),
            student_id=auth_data.student_id
        )

        rateable_employees = [
            y
            for y in emp_working_today
            if y['學號'] not in [
                x['評分對象']
                for x in voted_emp_week
            ]
        ]
        print(rateable_employees)

        if rateable_employees == []:

            logger.error(f'[AUTH {auth_data.student_id}] 目前沒有可評分的員工')

            raise HTTPException(404, "目前沒有可評分的員工")

        else:

            auth_response.rateable_employees = rateable_employees

            logger.info(
                f'[AUTH {auth_data.student_id}] Success! Returned data!')

            return auth_response
