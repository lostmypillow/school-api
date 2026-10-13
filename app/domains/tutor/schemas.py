"""Typed baseline schemas for MSSQL query return shapes in tutor domain.

These definitions document and type-check the exact dictionary shapes returned
by each named SQL script file under `app/core/sql/tutors/`.
"""
from datetime import datetime
from typing import TypedDict


class StudentSqlRow(TypedDict):
    """Shape returned by tutors/fetch_role_student.sql.

    SQL: SELECT name, student_id FROM dbo.students WHERE card_id = ? OR student_id = ?;
    """
    name: str | None
    student_id: str


class TeacherSqlRow(TypedDict):
    """Shape returned by tutors/fetch_role_teacher.sql.

    SQL: SELECT name, id, college, new_college FROM dbo.users
         WHERE card_id = ? OR id = ? AND department = '9';
    """
    name: str | None
    id: str
    college: str | None
    new_college: str | None


class AssociatedDeviceSqlRow(TypedDict):
    """Shape returned by tutors/fetch_associated_device.sql.

    SQL: SELECT id FROM dbo.devices WHERE teacher_id = ?;
    """
    id: int


class CheckDeviceTeacherSqlRow(TypedDict):
    """Shape returned by tutors/check_for_teacher.sql.

    SQL: SELECT teacher_id FROM dbo.devices WHERE id = ?;
    """
    teacher_id: str | None


class DeviceSqlRow(TypedDict):
    """Shape returned by tutors/select_device_db.sql.

    SQL: SELECT id, teacher_id FROM devices;
    """
    id: int
    teacher_id: str | None


class AppointmentSqlRow(TypedDict):
    """Shape returned by tutors/register_select.sql.

    SQL: SELECT id FROM dbo.tutor_appointments
         WHERE date = CONVERT(varchar, getdate(), 111)
           AND student_id = ? AND teacher_id = ? AND end_time IS NULL;
    """
    id: int


class AnnouncementSqlRow(TypedDict):
    """Shape returned by tutors/get_announce.sql.

    SQL: SELECT id, content, created_at, updated_at FROM math_announcements;
    """
    id: int
    content: str
    created_at: datetime
    updated_at: datetime | None
