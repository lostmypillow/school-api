from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crud import (
    get_existing_semester_ids,
    get_scraped_department_ids_for_classes,
    get_scraped_department_year_ids_for_courses,
    get_scraped_semester_ids_for_departments,
    save_ntut_operations,
)
from app.core.tables import Course, Department, DepartmentYear, Semester


@pytest.mark.asyncio
async def test_save_ntut_operations_semesters(test_session: AsyncSession):
    """Test save_ntut_operations saves and merges sem_list items."""
    payload = {
        "sem_list": [
            {
                "id": "112_1",
                "year": "112",
                "sem": "1",
                "link": "Subj.jsp?year=112&sem=1",
            },
            {
                "id": "112_2",
                "year": "112",
                "sem": "2",
                "link": "Subj.jsp?year=112&sem=2",
            },
        ]
    }

    await save_ntut_operations(test_session, payload)

    records = (await test_session.scalars(select(Semester))).all()
    assert len(records) == 2
    ids = {r.id for r in records}
    assert ids == {"112_1", "112_2"}
    assert all(r.created_at is not None for r in records)


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Bug in crud.py: Semester(**item, created_at=...) raises TypeError when item already has 'created_at'",
    strict=True,
)
async def test_save_ntut_operations_dict_with_timestamps_bug(test_session: AsyncSession):
    """Edge Case: Passing item with 'created_at' in payload to save_ntut_operations.

    Bug: **item unpacking conflicts with explicit keyword argument created_at=... raising TypeError.
    """
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    payload = {
        "sem_list": [
            {
                "id": "113_1",
                "year": "113",
                "sem": "1",
                "link": "link",
                "created_at": now,
            }
        ]
    }
    await save_ntut_operations(test_session, payload)


@pytest.mark.asyncio
async def test_save_ntut_operations_departments(test_session: AsyncSession):
    """Test save_ntut_operations saves and merges dep_list items."""
    # First ensure parent semester exists for FK
    sem = Semester(id="112_1", year="112", sem="1", link="link")
    test_session.add(sem)
    await test_session.commit()

    payload = {
        "dep_list": [
            {
                "id": "112_1_300",
                "semester_id": "112_1",
                "year": "112",
                "sem": "1",
                "code": "300",
                "name": "Dept CS",
                "link": "link_300",
            }
        ]
    }

    await save_ntut_operations(test_session, payload)

    records = (await test_session.scalars(select(Department))).all()
    assert len(records) == 1
    assert records[0].id == "112_1_300"
    assert records[0].name == "Dept CS"


@pytest.mark.asyncio
async def test_save_ntut_operations_department_years(test_session: AsyncSession):
    """Test save_ntut_operations saves and merges dep_year_list items."""
    sem = Semester(id="112_1", year="112", sem="1", link="link")
    dep = Department(
        id="112_1_300",
        semester_id="112_1",
        year="112",
        sem="1",
        code="300",
        name="Dept CS",
        link="link_300",
    )
    test_session.add_all([sem, dep])
    await test_session.commit()

    payload = {
        "dep_year_list": [
            {
                "id": "112_1_300_101",
                "department_id": "112_1_300",
                "year": "112",
                "sem": "1",
                "code": "101",
                "name": "CS Year 1",
                "link": "link_101",
            }
        ]
    }

    await save_ntut_operations(test_session, payload)

    records = (await test_session.scalars(select(DepartmentYear))).all()
    assert len(records) == 1
    assert records[0].id == "112_1_300_101"
    assert records[0].name == "CS Year 1"


@pytest.mark.asyncio
async def test_save_ntut_operations_courses(test_session: AsyncSession):
    """Test save_ntut_operations saves and merges course_list items."""
    sem = Semester(id="112_1", year="112", sem="1", link="link")
    dep = Department(
        id="112_1_300",
        semester_id="112_1",
        year="112",
        sem="1",
        code="300",
        name="Dept CS",
        link="link_300",
    )
    dy = DepartmentYear(
        id="112_1_300_101",
        department_id="112_1_300",
        year="112",
        sem="1",
        code="101",
        name="CS Year 1",
        link="link_101",
    )
    test_session.add_all([sem, dep, dy])
    await test_session.commit()

    payload = {
        "course_list": [
            {
                "id": "112_1_101_300001",
                "department_year_id": "112_1_300_101",
                "year": "112",
                "sem": "1",
                "code": "300001",
                "name": "Operating Systems",
                "credits": 3,
                "instructor": "Prof Linus",
                "classroom": "Lab 1",
                "students_enrolled": 45,
                "students_dropped": 1,
            }
        ]
    }

    await save_ntut_operations(test_session, payload)

    records = (await test_session.scalars(select(Course))).all()
    assert len(records) == 1
    assert records[0].id == "112_1_101_300001"
    assert records[0].name == "Operating Systems"


@pytest.mark.asyncio
async def test_save_ntut_operations_empty_payload(test_session: AsyncSession):
    """Test save_ntut_operations handles empty dictionary without crashing."""
    await save_ntut_operations(test_session, {})


@pytest.mark.asyncio
async def test_get_existing_semester_ids(test_session: AsyncSession):
    """Test get_existing_semester_ids returns set of all Semester IDs."""
    sem1 = Semester(id="111_1", year="111", sem="1", link="l1")
    sem2 = Semester(id="111_2", year="111", sem="2", link="l2")
    test_session.add_all([sem1, sem2])
    await test_session.commit()

    ids = await get_existing_semester_ids(test_session)
    assert ids == {"111_1", "111_2"}


@pytest.mark.asyncio
async def test_get_scraped_semester_ids_for_departments(test_session: AsyncSession):
    """Test get_scraped_semester_ids_for_departments returns distinct semester IDs from departments."""
    sem1 = Semester(id="112_1", year="112", sem="1", link="l1")
    sem2 = Semester(id="112_2", year="112", sem="2", link="l2")
    dep1 = Department(
        id="112_1_300",
        semester_id="112_1",
        year="112",
        sem="1",
        code="300",
        name="CS",
        link="l",
    )
    dep2 = Department(
        id="112_1_301",
        semester_id="112_1",
        year="112",
        sem="1",
        code="301",
        name="EE",
        link="l",
    )
    test_session.add_all([sem1, sem2, dep1, dep2])
    await test_session.commit()

    ids = await get_scraped_semester_ids_for_departments(test_session)
    assert ids == {"112_1"}


@pytest.mark.asyncio
async def test_get_scraped_department_ids_for_classes(test_session: AsyncSession):
    """Test get_scraped_department_ids_for_classes returns distinct department IDs from department years."""
    sem = Semester(id="112_1", year="112", sem="1", link="l")
    dep1 = Department(
        id="112_1_300",
        semester_id="112_1",
        year="112",
        sem="1",
        code="300",
        name="CS",
        link="l",
    )
    dep2 = Department(
        id="112_1_301",
        semester_id="112_1",
        year="112",
        sem="1",
        code="301",
        name="EE",
        link="l",
    )
    dy1 = DepartmentYear(
        id="112_1_300_101",
        department_id="112_1_300",
        year="112",
        sem="1",
        code="101",
        name="CS 1",
        link="l",
    )
    dy2 = DepartmentYear(
        id="112_1_300_102",
        department_id="112_1_300",
        year="112",
        sem="1",
        code="102",
        name="CS 2",
        link="l",
    )
    test_session.add_all([sem, dep1, dep2, dy1, dy2])
    await test_session.commit()

    ids = await get_scraped_department_ids_for_classes(test_session)
    assert ids == {"112_1_300"}


@pytest.mark.asyncio
async def test_get_scraped_department_year_ids_for_courses(test_session: AsyncSession):
    """Test get_scraped_department_year_ids_for_courses returns distinct department_year_ids from courses."""
    sem = Semester(id="112_1", year="112", sem="1", link="l")
    dep = Department(
        id="112_1_300",
        semester_id="112_1",
        year="112",
        sem="1",
        code="300",
        name="CS",
        link="l",
    )
    dy1 = DepartmentYear(
        id="112_1_300_101",
        department_id="112_1_300",
        year="112",
        sem="1",
        code="101",
        name="CS 1",
        link="l",
    )
    dy2 = DepartmentYear(
        id="112_1_300_102",
        department_id="112_1_300",
        year="112",
        sem="1",
        code="102",
        name="CS 2",
        link="l",
    )
    c1 = Course(
        id="112_1_101_300001",
        department_year_id="112_1_300_101",
        year="112",
        sem="1",
        code="300001",
        name="C1",
    )
    c2 = Course(
        id="112_1_101_300002",
        department_year_id="112_1_300_101",
        year="112",
        sem="1",
        code="300002",
        name="C2",
    )
    test_session.add_all([sem, dep, dy1, dy2, c1, c2])
    await test_session.commit()

    ids = await get_scraped_department_year_ids_for_courses(test_session)
    assert ids == {"112_1_300_101"}
