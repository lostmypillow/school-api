from datetime import datetime

from pydantic import BaseModel


class AddAnnouncement(BaseModel):
    content: str


class UpdateAnnouncement(BaseModel):
    id: int | None
    content: str


class Announcement(AddAnnouncement):
    id: int | None
    created_at: datetime | None
    updated_at: datetime | None
