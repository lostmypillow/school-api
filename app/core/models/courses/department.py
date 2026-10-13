from datetime import datetime, UTC

from sqlalchemy import Unicode, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.models.base import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(Unicode(64), primary_key=True)
    semester_id: Mapped[str] = mapped_column(
        Unicode(36), ForeignKey("semesters.id", ondelete="CASCADE")
    )
    year:Mapped[str] = mapped_column(Unicode(10))
    sem: Mapped[str] = mapped_column(Unicode(10))
    code: Mapped[str] = mapped_column(Unicode(20))
    name: Mapped[str] = mapped_column(Unicode(255))
    link: Mapped[str] = mapped_column(Unicode(2048))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint("year", "sem", "code", name="uq_departments_year_sem_code"),
    )

    semester_rel = relationship(argument="Semester", back_populates="departments")
    classes = relationship(argument="DepartmentYear", back_populates="department_rel")
