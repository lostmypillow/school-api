from datetime import datetime, UTC

from sqlalchemy import Column, Unicode, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.tables.base import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column[str](Unicode(64), primary_key=True)  # Slug: e.g., "112_1_01"
    semester_id = Column[str](
        Unicode(36), ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False
    )
    year = Column[str](Unicode(10), nullable=False)
    sem = Column[str](Unicode(10), nullable=False)
    code = Column[str](Unicode(20), nullable=False)
    name = Column[str](Unicode(255), nullable=False)
    link = Column[str](Unicode(2048), nullable=False)
    created_at = Column[datetime](
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at = Column[datetime](
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("year", "sem", "code", name="uq_departments_year_sem_code"),
    )

    semester_rel = relationship(argument="Semester", back_populates="departments")
    classes = relationship(argument="DepartmentYear", back_populates="department_rel")
