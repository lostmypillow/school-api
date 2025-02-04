from fastapi import APIRouter, HTTPException
from typing import  Literal
from pydantic import BaseModel
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

    course: str
        班別

    course_num: int
        主檔號

    type: Literal['seats', 'survey']
        not to be confused with python types, either 'seats' or 'survey'
    """
    student_id: str
    type: Literal['seats', 'survey']


class AuthResponse(BaseModel):
    學號: str
    姓名: str
    性別: str
    rateable_employees: list = []


{
    "student_id": "",
    "course": "",
    "course_num": 4,
    "type": "survey"
}


@auth_router.post('/')
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
    logger.info(f'[AUTH {auth_data.student_id}] Processing auth data...')

    
    student_details: dict[str, str] = await exec_sql(
            'one',
            'student_details',
            card_id=auth_data.student_id
        )
        # OUTPUT:
        # {
        #     "學號": "",
        #     "姓名": "",
        #     "性別": "男"
        # }

    auth_response = AuthResponse(**student_details)

    if student_details and auth_data.type == "seats":

            logger.info(
                f'''[AUTH {auth_data.student_id}] Student details exist & auth is for seats''')

            courses_of_student: list[dict[str, str]] = await exec_sql(
                'all',
                'student_match_course',
                student_id=auth_data.student_id
            )
            # OUTPUT:
            # [
            #     {
            #         "班別": ""
            #     }
            # ]
            class_with_seat = await get_class_with_seats()

            matches_course: bool = any(
                d['班別'] == class_with_seat['班別']
                for d in courses_of_student
            )

            logger.info(
                f'''[AUTH {auth_data.student_id}] Student s course matches course for seats'''
                if matches_course else
                f'''[AUTH {auth_data.student_id}] Student s courses match course for seats'''
            )

            check_already_selected: list = await exec_sql(
                'all',
                'student_already_selected',
                course_id=class_with_seat['主檔號'],
                student_id=auth_data.student_id
            )
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
                f'[AUTH {auth_data.student_id}] Student has not already selected seat for course')

            if not matches_course or already_selected:

                logger.error(f'[AUTH {auth_data.student_id}] 目前沒有您可選的補位資料')

                raise HTTPException(404, "目前沒有您可選的補位資料")

            else:

                logger.info(
                    f'[AUTH {auth_data.student_id}] Success! Returned data!')

                return auth_response

    elif student_details and auth_data.type == "survey":

            logger.info(
                f'[AUTH {auth_data.student_id}] Student details exist and auth is for survey')

            if settings.DEBUG is True:
                 logger.info('debug mode is on')
            else:
                 logger.info('DEBUG mode is not on')
            emp_working_today = await exec_sql(
                'all',
                'student_today_employees',
                current_date='2020-09-16'
            )
            # TODO replace debug values: datetime.now().strftime('%Y-%m-%d')

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
                monday=(datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d 00:00:00.000'),
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

    else:

            logger.error(f'[AUTH {auth_data.student_id}] 查無此人')

            raise HTTPException(404, "查無此人")
