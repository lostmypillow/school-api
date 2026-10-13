from typing import Optional

from sqlalchemy import String, Unicode, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str]  = mapped_column(String(20), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(Unicode(50))
    card_id: Mapped[Optional[str]] = mapped_column(String(20))
    college: Mapped[Optional[str]] = mapped_column(Unicode(50))
    new_college: Mapped[Optional[str]] = mapped_column(Unicode(50))
    department: Mapped[Optional[str]] = mapped_column(String(10))

    # Department code 2, 4, 8, 9, or 11 as mapped in deps.py, queried by get_dep_number.sql and student_today_employees.sql
    main_department: Mapped[int] = mapped_column(Integer)

    # Must be <> 1 for eligible survey targets, queried by student_today_employees.sql
    job_type: Mapped[int] = mapped_column(Integer)