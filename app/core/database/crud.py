from app.core.database.models import Course
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.models import Department, DepartmentYear, Semester


async def save_ntut_operations(db: AsyncSession, payload: dict) -> None:
    """Pure DB function: Upserts payload into SQLite or PostgreSQL seamlessly."""
    now = datetime.now(UTC)

    if payload.get("sem_list"):
        for item in payload["sem_list"]:
            semester = Semester(
                **item,
                created_at=item.get("created_at") or now,
                updated_at=item.get("updated_at") or now,
            )
            await db.merge(semester)

    elif payload.get("dep_list"):
        for d in payload["dep_list"]:
            department = Department(
                **d,
                created_at=d.get("created_at") or now,
                updated_at=d.get("updated_at") or now,
            )
            await db.merge(department)

    elif payload.get("dep_year_list"):
        for c in payload["dep_year_list"]:
            dep_year = DepartmentYear(
                **c,
                created_at=c.get("created_at") or now,
                updated_at=c.get("updated_at") or now,
            )
            await db.merge(dep_year)

    elif payload.get("course_list"):
        for c in payload["course_list"]:
            course = Course(
                **c,
                created_at=c.get("created_at") or now,
                updated_at=c.get("updated_at") or now,
            )
            await db.merge(course)
    await db.commit()


async def get_existing_semester_ids(db: AsyncSession) -> set[str]:
    """Returns a set of existing semester IDs."""
    results = (await db.execute(select(Semester.id))).all()
    return {r[0] for r in results}


async def get_scraped_semester_ids_for_departments(db: AsyncSession) -> set[str]:
    """Returns a set of semester IDs that already have departments in DB."""
    results = (await db.execute(select(Department.semester_id).distinct())).all()
    return {r[0] for r in results}


async def get_scraped_department_ids_for_classes(db: AsyncSession) -> set[str]:
    """Returns a set of department IDs that already have classes in DB."""
    results = await db.scalars(select(DepartmentYear.department_id).distinct())
    return {r for r in results.all() if r is not None}


async def get_scraped_department_year_ids_for_courses(db: AsyncSession) -> set[str]:
    """Returns a set of department IDs that already have classes in DB."""
    results = (await db.execute(select(Course.department_year_id).distinct())).all()

    return {r[0] for r in results}
