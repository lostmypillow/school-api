from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Department, DepartmentYear, Semester


async def save_api_payload(db: AsyncSession, payload: dict) -> None:
    """Pure DB function: Upserts payload into SQLite or PostgreSQL seamlessly."""
    dialect_name = db.get_bind().dialect.name
    now = datetime.now(UTC)

    if dialect_name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert

    # 1. Semesters (Insert missing, ignore existing)
    if payload.get("sem_list"):
        sem_data = [
            {
                **s,
                "created_at": s.get("created_at") or now,
                "updated_at": s.get("updated_at") or now,
            }
            for s in payload["sem_list"]
        ]
        stmt = insert(Semester).values(sem_data)
        upsert_sem = stmt.on_conflict_do_nothing(index_elements=["id"])
        await db.execute(upsert_sem)

    # 2. Departments (Insert missing, update all fields on conflict)
    if payload.get("dep_list"):
        deps = [
            {
                **d,
                "created_at": d.get("created_at") or now,
                "updated_at": d.get("updated_at") or now,
            }
            for d in payload["dep_list"]
            if d.get("id") and d.get("code") and d.get("year") and d.get("sem")
        ]
        if deps:
            stmt = insert(Department).values(deps)
            upsert_dep = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "semester_id": stmt.excluded.semester_id,
                    "name": stmt.excluded.name,
                    "link": stmt.excluded.link,
                    "html_content": stmt.excluded.html_content,
                    "updated_at": now,  # Explicitly refresh timestamp on conflict
                },
            )
            await db.execute(upsert_dep)

    # 3. Department Classes (Insert missing, update all fields on conflict)
    if payload.get("dep_year_list"):
        classes = [
            {
                **c,
                "created_at": c.get("created_at") or now,
                "updated_at": c.get("updated_at") or now,
            }
            for c in payload["dep_year_list"]
            if c.get("id") and c.get("code") and c.get("year") and c.get("sem")
        ]
        if classes:
            stmt = insert(DepartmentYear).values(classes)
            upsert_class = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "department_id": stmt.excluded.department_id,
                    "name": stmt.excluded.name,
                    "link": stmt.excluded.link,
                    "html_content": stmt.excluded.html_content,
                    "updated_at": now,
                },
            )
            await db.execute(upsert_class)

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
    results = (await db.execute(select(DepartmentYear.department_id).distinct())).all()
    
    return {r[0] for r in results}