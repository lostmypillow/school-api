from datetime import datetime

from sqlalchemy import Column, Unicode, ForeignKey, Integer, UnicodeText, DateTime, UniqueConstraint, text
from sqlalchemy.orm import relationship

from app.core.tables.base_model  import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column[str](Unicode(64), primary_key=True)  # Slug: e.g., "112_1_301_CS101"
    department_year_id = Column[str](
        Unicode(64),
        ForeignKey(column="department_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    year = Column[str](Unicode(10), nullable=False)
    sem = Column[str](Unicode(10), nullable=False)
    code = Column[str](Unicode(50), nullable=True)
    name = Column[str](Unicode(255), nullable=False)
    link = Column[str](Unicode(2048), nullable=True)
    credits = Column[int](Integer, nullable=True)
    course_type = Column[str](Unicode(20), nullable=True)
    instructor = Column[str](Unicode(255), nullable=True)

    # Schedule & Location
    sun = Column[str](Unicode(50), nullable=True)
    mon = Column[str](Unicode(50), nullable=True)
    tue = Column[str](Unicode(50), nullable=True)
    wed = Column[str](Unicode(50), nullable=True)
    thu = Column[str](Unicode(50), nullable=True)
    fri = Column[str](Unicode(50), nullable=True)
    sat = Column[str](Unicode(50), nullable=True)
    classroom = Column[str](Unicode(255), nullable=True)

    # Metrics & Metadata
    students_enrolled = Column[int](Integer, nullable=True)
    students_dropped = Column[int](Integer, nullable=True)
    language = Column[str](Unicode(50), nullable=True)
    notes = Column[str](UnicodeText, nullable=True)
    with_class = Column[str](Unicode(255), nullable=True)
    experiment = Column[str](Unicode(255), nullable=True)
    cross_discipline = Column[str](Unicode(255), nullable=True)

    created_at = Column[datetime](
        DateTime(timezone=True),
        server_default=text("SYSDATETIMEOFFSET()"),
        nullable=False,
    )
    updated_at = Column[datetime](
        DateTime(timezone=True),
        server_default=text("SYSDATETIMEOFFSET()"),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("id", name="uq_courses_year_sem_code"),)

    department_year_rel = relationship(argument="DepartmentYear", back_populates="courses")
