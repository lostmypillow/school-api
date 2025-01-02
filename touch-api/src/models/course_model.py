from ..database import execute_SQL
from ..models.student_model import Student
from pydantic import BaseModel
from typing import List, Optional
from pydantic import Field

# class Course:

#     def __init__(self):
#         self.main_number = None
#         self.male_seats = []
#         self.female_seats = []
#         self.name = None
#         self.other_name = None
#         self.seats = None
#         self._check_availability()

#     def _check_availability(self):
#         # def getSeatInfo(self):
#         # def is_seat_system_available(self):
#         result = execute_SQL('seats/remaining', 'one')
#         print(result)
#         if result:
#             self.main_number = result[0]
#             self.name = result[3]
#             self.other_name = result[4]
#             results = execute_SQL('course/get_remaining_seats', 'all')
#             if results:
#                 for res in results:
#                     if int(res[1][1:]) <= 15:
#                         self.female_seats.append({"sn":res[0], "name": res[1]})
#                     else:
#                         self.male_seats.append({"sn":res[0], "name": res[1]})



#     def register_student(self, student: Student):
#         execute_SQL('student/register_seat',
#                     'commit',
#                     student_id=student.student_id,
#                     sn=self.class_details.sn
#                     )
#     @property
#     def is_available(self):
#         return bool(self.male_seats and self.female_seats)
        
class Course(BaseModel):
    main_number: Optional[int] = None
    # Using a list of dictionaries for seats
    male_seats: List[dict] = Field(default_factory=list)
    # Using a list of dictionaries for seats
    female_seats: List[dict] = Field(default_factory=list)
    name: Optional[str] = None
    other_name: Optional[str] = None
    seats: Optional[int] = None

    class Config:
        # Use orm_mode to allow for compatibility with data from SQLAlchemy or other ORM sources
        orm_mode = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # Ensure Pydantic BaseModel initialization
        self._check_availability()

    def _check_availability(self):
        """Check the availability of seats."""
        result = execute_SQL('seats/remaining', 'one')
        if result:
            self.main_number = result[0]
            self.name = result[3]
            self.other_name = result[4]
            results = execute_SQL('course/get_remaining_seats', 'all')
            if results:
                for res in results:
                    if int(res[1][1:]) <= 15:
                        self.female_seats.append({"sn": res[0], "name": res[1]})
                    else:
                        self.male_seats.append({"sn": res[0], "name": res[1]})

    @property
    def is_available(self) -> bool:
        """Check if the course has available seats."""
        return bool(self.male_seats and self.female_seats)
