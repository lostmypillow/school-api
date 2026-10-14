from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped

from app.core.tables.base import Base


class EmployeeClockRecords(Base):
    __tablename__ = "employee_clock_records"

    student_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    clock_in_date: Mapped[str] = mapped_column(String(10), primary_key=True)