from typing import TypedDict


class AppointmentSqlRow(TypedDict):
    """Shape returned by tutors/register_select.sql.

    SQL: SELECT id FROM dbo.tutor_appointments
         WHERE date = CONVERT(varchar, getdate(), 111)
           AND student_id = ? AND teacher_id = ? AND end_time IS NULL;
    """
    id: int
