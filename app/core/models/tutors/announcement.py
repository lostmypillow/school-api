from sqlalchemy import Column, DateTime, Integer, UnicodeText, text

from app.core.models.base_model import Base


class Announcement(Base):
    __tablename__ = "math_announcements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(UnicodeText, nullable=False)
    created_at = Column(DateTime, server_default=text("SYSDATETIME()"), nullable=False)
    updated_at = Column(DateTime, nullable=True)
