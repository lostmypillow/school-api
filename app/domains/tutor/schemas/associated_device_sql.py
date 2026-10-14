from typing import TypedDict


class AssociatedDeviceSqlRow(TypedDict):
    """Shape returned by tutors/fetch_associated_device.sql.

    SQL: SELECT id FROM dbo.devices WHERE teacher_id = ?;
    """
    id: int
