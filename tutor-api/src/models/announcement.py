from pydantic import BaseModel
from datetime import datetime
class AddAnnouncement(BaseModel):
    content: str
    author: str
    

class Announcement(AddAnnouncement):
    id: int | None
    created_at: datetime | None
    updated_at: datetime | None

