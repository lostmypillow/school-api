from sqlalchemy import Integer, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tables.base import Base


class LegacyCourseNum(Base):
    __table_name__="legacy_course_num"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    legacy_course_num: Mapped[str] = mapped_column(Unicode(20))