from typing import TypedDict


class StudentSqlRow(TypedDict):
    """Shape returned by tutors/fetch_role_student.sql.

    SQL: SELECT name, student_id FROM dbo.students WHERE card_id = ? OR student_id = ?;
    """
    name: str | None
    student_id: str
