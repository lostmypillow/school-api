from typing import Annotated, Any

from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel
from ..models.student_model import Student
import pprint
router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


class AuthData(BaseModel):
    student_id: str
    course: Any
    type: str

@router.post('/')
def check_student(auth_data: AuthData):
    # print(auth_data.course['main_number'])
    # print(type(auth_data.course))
    # return ""
    try:
        student = Student(auth_data)
        if auth_data.type == "seats":
            student.check_match_class(auth_data.course['main_number'], auth_data.course['other_name'])
        elif auth_data.type == "survey":
            student.check_rateable_employees()

        
    except HTTPException as e:
        raise e
    return student
