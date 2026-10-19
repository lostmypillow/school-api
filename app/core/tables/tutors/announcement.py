from datetime import datetime

from sqlalchemy import DateTime, Integer, UnicodeText, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tables.base import Base


class Announcement(Base):
    __tablename__ = "math_announcements"

    id: Mapped[int] =  mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] =  mapped_column(UnicodeText, nullable=False)
    created_at: Mapped[datetime] =  mapped_column(DateTime, server_default=text("SYSDATETIME()"), nullable=False)
    updated_at: Mapped[datetime]=  mapped_column(DateTime, nullable=True)
