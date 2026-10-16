"""Unit tests for scrape_to_parquet in Tasks domain."""
from anyio import Path
import pytest
from unittest.mock import AsyncMock, patch

from app.domains.courses.schemas import (
    CourseModel,
    DepartmentModel,
    DepartmentYearModel,
    SemesterModel,
)
from app.domains.tasks.parquet_utils import (
    append_to_parquet,
    read_parquet_records,
)
from app.domains.tasks.scrape import scrape_to_parquet


@pytest.fixture
def mock_client():
    """Provides a mocked HTTP client for unit tests."""
    client = AsyncMock()
    client.is_closed = False
    return client


@pytest.mark.asyncio
async def test_scrape_to_parquet_orchestration(
    temp_parquet_dir: Path,
    mock_client: AsyncMock,
):
    """Unit test: verifies scrape_to_parquet orchestrates each pipeline step, writes Parquet snapshots, and cleans up client."""
    parquet_path = Path(temp_parquet_dir)

    sample_semester = SemesterModel(
        id="113_1",
        year="113",
        sem="1",
        link="Subj.jsp?format=-2&year=113&sem=1",
    )
    sample_dept = DepartmentModel(
        id="113_1_001",
        semester_id="113_1",
        year="113",
        sem="1",
        code="001",
        name="機電學院",
        link="Subj.jsp?format=-3&year=113&sem=1&code=001",
    )
    sample_dy = DepartmentYearModel(
        id="113_1_001_0482",
        department_id="113_1_001",
        year="113",
        sem="1",
        code="0482",
        name="跨校選課(大)",
        link="Subj.jsp?format=-4&year=113&sem=1&code=482",
    )
    sample_course = CourseModel(
        id="113_1_001_0482_123456",
        department_year_id="113_1_001_0482",
        year="113",
        sem="1",
        code="123456",
        name="測試課程",
        credits=3,
        course_type="必修",
        instructor="測試教師",
        link="ShowSyllabus.jsp?snum=123456",
    )

    async def fake_sync_semesters(parquet_dir, semester_list):
        await append_to_parquet("semesters", [sample_semester], parquet_dir)
        return [sample_semester]

    async def fake_scrape_departments(ctx, parquet_dir, sems_to_scrape, seen_dep_ids, chunk_size):
        await append_to_parquet("departments", [sample_dept], parquet_dir)
        return [sample_dept]

    async def fake_scrape_department_years(ctx, parquet_dir, departments_to_scrape, seen_class_ids, chunk_size):
        await append_to_parquet("department_years", [sample_dy], parquet_dir)
        return [sample_dy]

    async def fake_scrape_courses(ctx, parquet_dir, dep_years_to_scrape, chunk_size):
        await append_to_parquet("courses", [sample_course], parquet_dir)
        return [sample_course]

    async def fake_scrape_courses_syllabi(ctx, parquet_dir, course_to_scrape, chunk_size):
        return []

    ctx = {
        "parquet_dir": parquet_path,
        "client": mock_client,
    }

    with patch("app.domains.tasks.scrape.main.sync_semesters", side_effect=fake_sync_semesters) as mock_sync_sem, \
         patch("app.domains.tasks.scrape.main.scrape_departments", side_effect=fake_scrape_departments) as mock_scrape_dept, \
         patch("app.domains.tasks.scrape.main.scrape_department_years", side_effect=fake_scrape_department_years) as mock_scrape_dy, \
         patch("app.domains.tasks.scrape.main.scrape_courses", side_effect=fake_scrape_courses) as mock_scrape_courses, \
         patch("app.domains.tasks.scrape.main.scrape_courses_syllabi", side_effect=fake_scrape_courses_syllabi) as mock_scrape_syllabi:

        await scrape_to_parquet(ctx=ctx)

        # Verify orchestration calls
        mock_sync_sem.assert_called_once()
        mock_scrape_dept.assert_called_once()
        mock_scrape_dy.assert_called_once()
        mock_scrape_courses.assert_called_once()
        mock_scrape_syllabi.assert_called_once()

    # 1. Verify semesters.parquet created and contains valid records
    sem_file = parquet_path / "semesters.parquet"
    assert await sem_file.exists(), "semesters.parquet should exist in disposable dir"
    sem_records = await read_parquet_records(sem_file)
    assert len(sem_records) == 1
    for r in sem_records:
        SemesterModel.model_validate(r)

    # 2. Verify departments.parquet created and contains valid records
    dept_file = parquet_path / "departments.parquet"
    assert await dept_file.exists(), "departments.parquet should exist in disposable dir"
    dept_records = await read_parquet_records(dept_file)
    assert len(dept_records) == 1
    for r in dept_records:
        DepartmentModel.model_validate(r)

    # 3. Verify department_years.parquet created and contains valid records
    dy_file = parquet_path / "department_years.parquet"
    assert await dy_file.exists(), "department_years.parquet should exist in disposable dir"
    dy_records = await read_parquet_records(dy_file)
    assert len(dy_records) == 1
    for r in dy_records:
        DepartmentYearModel.model_validate(r)

    # 4. Verify courses.parquet created and contains valid records
    course_file = parquet_path / "courses.parquet"
    assert await course_file.exists(), "courses.parquet should exist in disposable dir"
    course_records = await read_parquet_records(course_file)
    assert len(course_records) == 1
    for r in course_records:
        CourseModel.model_validate(r)

    # Verify client cleanup
    mock_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_scrape_to_parquet_instantiates_and_closes_default_client(
    temp_parquet_dir: Path,
):
    """Unit test: verifies scrape_to_parquet creates a default client when omitted from ctx and closes it."""
    mock_client_instance = AsyncMock()
    mock_client_instance.is_closed = False

    ctx = {"parquet_dir": Path(temp_parquet_dir)}

    with patch("app.domains.tasks.scrape.main.CustomAsyncClient", return_value=mock_client_instance) as mock_cls, \
         patch("app.domains.tasks.scrape.main.sync_semesters", new_callable=AsyncMock, return_value=[]), \
         patch("app.domains.tasks.scrape.main.scrape_departments", new_callable=AsyncMock), \
         patch("app.domains.tasks.scrape.main.scrape_department_years", new_callable=AsyncMock), \
         patch("app.domains.tasks.scrape.main.scrape_courses", new_callable=AsyncMock), \
         patch("app.domains.tasks.scrape.main.scrape_courses_syllabi", new_callable=AsyncMock):

        await scrape_to_parquet(ctx=ctx)

        mock_cls.assert_called_once()
        mock_client_instance.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_scrape_to_parquet_exception_handling_and_cleanup(
    temp_parquet_dir: Path,
    mock_client: AsyncMock,
):
    """Unit test: verifies scrape_to_parquet re-raises errors and properly cleans up client on error."""
    ctx = {
        "parquet_dir": Path(temp_parquet_dir),
        "client": mock_client,
    }

    with patch(
        "app.domains.tasks.scrape.main.sync_semesters",
        side_effect=RuntimeError("Simulated sync error"),
    ):
        with pytest.raises(RuntimeError, match="Simulated sync error"):
            await scrape_to_parquet(ctx=ctx)

    mock_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_scrape_to_parquet_incremental_filtering(
    temp_parquet_dir: Path,
    mock_client: AsyncMock,
):
    """Unit test: verifies scrape_to_parquet skips already-scraped semesters/departments."""
    parquet_path = Path(temp_parquet_dir)

    # Pre-populate departments with an existing past semester ("86_1")
    old_dept = DepartmentModel(
        id="86_1_001",
        semester_id="86_1",
        year="86",
        sem="1",
        code="001",
        name="舊學期學院",
        link="Subj.jsp?format=-3&year=86&sem=1&code=001",
    )
    await append_to_parquet("departments", [old_dept], parquet_path)

    # Sync semesters returns the old semester and a new one
    old_sem = SemesterModel(id="86_1", year="86", sem="1", link="Subj.jsp?year=86&sem=1")
    new_sem = SemesterModel(id="99_1", year="99", sem="1", link="Subj.jsp?year=99&sem=1")

    ctx = {
        "parquet_dir": parquet_path,
        "client": mock_client,
    }

    with patch("app.domains.tasks.scrape.main.sync_semesters", new_callable=AsyncMock, return_value=[old_sem, new_sem]), \
         patch("app.domains.tasks.scrape.main.scrape_departments", new_callable=AsyncMock) as mock_scrape_dept, \
         patch("app.domains.tasks.scrape.main.scrape_department_years", new_callable=AsyncMock), \
         patch("app.domains.tasks.scrape.main.scrape_courses", new_callable=AsyncMock), \
         patch("app.domains.tasks.scrape.main.scrape_courses_syllabi", new_callable=AsyncMock):

        await scrape_to_parquet(ctx=ctx)

        mock_scrape_dept.assert_called_once()
        passed_sems = mock_scrape_dept.call_args.kwargs["sems_to_scrape"]
        passed_sem_ids = {s.id for s in passed_sems}

        # 86_1 was already in departments.parquet and is not current semester, so it must be skipped
        assert "86_1" not in passed_sem_ids
        assert "99_1" in passed_sem_ids

