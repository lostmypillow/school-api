from typing import TypedDict


class DeviceSqlRow(TypedDict):
    """Shape returned by tutors/select_device_db.sql.

    SQL: SELECT id, teacher_id FROM devices;
    """
    id: int
    teacher_id: str | None
