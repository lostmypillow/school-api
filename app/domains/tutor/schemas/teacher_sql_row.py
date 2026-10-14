from typing import TypedDict


class TeacherSqlRow(TypedDict):
    """Shape returned by tutors/fetch_role_teacher.sql.

    SQL: SELECT name, id, college, new_college FROM dbo.users
         WHERE card_id = ? OR id = ? AND department = '9';
    """
    name: str | None
    id: str
    college: str | None
    new_college: str | None
