from datetime import datetime
from typing import TypedDict


class AnnouncementSqlRow(TypedDict):
    """Shape returned by tutors/get_announce.sql.

    SQL: SELECT id, content, created_at, updated_at FROM math_announcements;
    """
    id: int
    content: str
    created_at: datetime
    updated_at: datetime | None
