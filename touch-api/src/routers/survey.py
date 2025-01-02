from ..models.employee_model import Employee
from ..models.student_model import Student
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel


class SurveyResult(BaseModel):
    employee_id: str
    student_id: str
    rating: int


router = APIRouter(
    prefix="/survey",
    tags=["Survey"],
)


@router.get('/employees/{student_id}')
def get_employees(student_id: str):
    try:
        working_employees = Employee.working_today(
            Student(student_id).voted_employees)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="發生錯誤")
    return working_employees


@router.post('/')
def send_survey(result: SurveyResult):
    try:
        print(result)
        Student.rate(result.student_id,
                     Employee(result.employee_id), result.rating)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    return "填寫完成"
