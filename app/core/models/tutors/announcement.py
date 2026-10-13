from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, UnicodeText, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models.base import Base


class Announcement(Base):
    __tablename__ = "math_announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(UnicodeText)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("SYSDATETIME()"))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
