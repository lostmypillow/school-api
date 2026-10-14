from typing import TypedDict


class CheckDeviceTeacherSqlRow(TypedDict):
    """Shape returned by tutors/check_for_teacher.sql.

    SQL: SELECT teacher_id FROM dbo.devices WHERE id = ?;
    """
    teacher_id: str | None
