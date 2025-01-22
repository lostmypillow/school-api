from fastapi import APIRouter, HTTPException
from typing import Any
from pydantic import BaseModel
from lib.auth_operations import check_existence, check_match, check_already_selected, check_rateable_employees

from database.async_operations import exec_sql

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


class AuthData(BaseModel):
    student_id: str
    course: str
    course_num: int
    type: str


# {
#   "student_id": "",
#   "course": "",
#   "course_num": 4,
#   "type": "survey"
# }

@router.post('/')
async def check_student(auth_data: AuthData):
    """_summary_

    Parameters
    ----------
    auth_data : AuthData
        _description_

    Returns
    -------
    _type_
        _description_

    Raises
    ------
    HTTPException
        _description_
    """

    try:
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

        if student_details and auth_data.type == "seats":
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

            matches_course: bool = any(
                d['班別'] == auth_data.course for d in courses_of_student)

            check_already_selected: list = await exec_sql(
                'all',
                'student_already_selected',
                course_id=4,
                student_id='30003'
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

            if matches_course or already_selected:
                raise HTTPException(404, "目前沒有您可選的補位資料")
            else:
                return student_details

        elif student_details and auth_data.type == "survey":
            deps = {
                : 2,
                "": 4,
                : 8,
                : 9,
                : 11
            }
            emp_working_today = await exec_sql(
                'all',
                'student_today_employees',
                current_date='2020-09-16'
            )

            for employee in emp_working_today:
                if "學號" in employee:
                    employee['學號'] = employee['學號'].strip()
                #
                if '主要部門' in employee:
                    employee['主要部門'] = next(
                        (k for k, v in deps.items() if v == employee['主要部門']), None)
            
            voted_emp_week = await exec_sql(
                'all',
                'student_voted_employees',
                monday='2020-12-15 00:00:00.000',
                student_id=''
            )
            
            rateable_employees =  [y for y in emp_working_today if y['學號'] not in {x['評分對象'] for x in voted_emp_week}]

            if rateable_employees == []:
                raise HTTPException(404, "目前沒有可評分的員工")
            else:
                student_details["rateable_employees"] = rateable_employees
                return student_details

        else:
            raise HTTPException(404, "查無此人")

    except Exception as e:
        print(e)
        raise HTTPException(404, "發生錯誤")